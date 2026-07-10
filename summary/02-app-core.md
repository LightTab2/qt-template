# Application core (Qt UI, exceptions, QML) - analysis

## Purpose
This subsystem is the runnable heart of the Qt6 template: the `main()` entry
point, the single `QMainWindow` subclass it shows, and a small exception /
logging layer that funnels every Qt diagnostic (`qDebug`/`qInfo`/`qWarning`/
`qCritical`/`qFatal`) through one handler that both logs to `stderr` and pops a
`QMessageBox`. It solves the "give me a working, exception-safe Qt Widgets app
skeleton" problem: a booted `QApplication`, a shown window, a global error
funnel, and a four-tier catch ladder around the event loop. Much of the code in
this domain is deliberately illustrative (Doxygen-demo symbols, dependency
"smoke" lines) rather than functional, so the real load-bearing surface is
smaller than the file count suggests.

## Owned paths
This domain owns the application sources and the tests that link the app library:

- `src/main.cpp` - entry point, `QApplication` bootstrap, catch ladder, `befriendedFunction`.
- `src/mainwindow.h`, `src/mainwindow.cpp` - the `MainWindow` widget class.
- `src/mainwindow.ui` - Qt Designer form consumed by AUTOUIC -> `ui_mainwindow.h`.
- `src/Exceptions/Exceptions.h`, `src/Exceptions/Exceptions.cpp` - `AppException`, `ErrorType`, `errorMessageHandler`, `operator<<(QDebug, ErrorType)`, `ERROR_MESSAGE` macro.
- `src/qml/**` - QML source root (currently only a placeholder file; see below).
- `test/testTest.cpp`, `test/gslLinkTest.cpp`, `test/integrationSmokeTest.cpp` - the Qt Test executables that exercise this domain.

Shared / boundary paths (NOT solely owned here, flag for the build domain):
- `CMakeLists.txt`, `cmake/Sources.cmake`, `cmake/Resources.cmake`, `cmake/Modules.cmake`, `cmake/StandardSettings.cmake`, `test/CMakeLists.txt` - the build/deps domain owns these; this report only reads them to explain AUTOMOC/AUTOUIC/AUTORCC and the two-target wiring.
- `icon/**` - resource assets referenced by `MainWindow` and `Resources.cmake`; owned by the build/resources domain.
- The `src/qml/` glob is also consumed by `cmake/Resources.cmake` (QML module wiring) - shared surface with the build domain.

## Key files & symbols

| File | Central symbol | One line |
| --- | --- | --- |
| `src/main.cpp:11` | `int main(int, char**)` | Boots `QApplication`, installs the message handler, shows `MainWindow`, runs the event loop under a catch ladder that returns `EXIT_FAILURE` on error; supports `--self-test`. |
| `src/main.cpp:10` | `showExceptionMessageBox` (lambda) | Wraps `QMessageBox::critical(nullptr, "Critical", message)` used by the event-loop catches. |
| `src/main.cpp:138` | `befriendedFunction(MainWindow)` | Doxygen `friend` demo; calls `win.func2(12)`; never invoked in the live build. |
| `src/mainwindow.h:28` | `class MainWindow : public QMainWindow` | The one real widget; `Q_OBJECT`, owns a `Ui::MainWindow* ui`. |
| `src/mainwindow.cpp:8` | `MainWindow::MainWindow(QWidget*)` | `new Ui::MainWindow`, `setupUi`, sets window icon + title "Qt Template". |
| `src/mainwindow.cpp:18` | `MainWindow::~MainWindow()` | `delete ui`. |
| `src/mainwindow.ui:3` | `<class>MainWindow` form | 709x550 window, `centralWidget` with a `QVBoxLayout`, a `menuBar`, a `statusBar`. |
| `src/Exceptions/Exceptions.h:21` | `enum class ErrorType` | Error taxonomy in "XXZZ" (category/subcategory) format; currently `Invalid=0`, `General=1`. |
| `src/Exceptions/Exceptions.h:29` | `class AppException : public QException` | Project exception distinguishing app-thrown from Qt-thrown `QException`s; carries `const ErrorType errorType`. |
| `src/Exceptions/Exceptions.h:17` | `#define ERROR_MESSAGE(msg) showMessage()` | Widgets-mode alias; note it DISCARDS its argument (see Gotchas). |
| `src/Exceptions/Exceptions.cpp:27` | `operator<<(QDebug, const ErrorType&)` | The real "ErrorType -> string" mapping (a `switch`, not an array). |
| `src/Exceptions/Exceptions.cpp:41` | `errorMessageHandler(QtMsgType, const QMessageLogContext&, QString)` | The installed Qt message handler: formats, logs (`_DEBUG`-gated), shows a box, and throws `AppException` on Critical/Fatal. |

## Architecture & responsibilities
Three cooperating layers:

1. **Bootstrap / lifecycle** (`main.cpp`) - owns process startup, the
   `QApplication` object (held in a `std::unique_ptr`), org/app-name metadata,
   installing the global message handler, constructing and showing `MainWindow`,
   and running/terminating the event loop.
2. **UI** (`mainwindow.*`, `mainwindow.ui`) - owns the top-level window. The
   header is largely a Doxygen showcase; the only functional members are the
   ctor/dtor and the `ui` pointer.
3. **Error / logging funnel** (`Exceptions/*`) - owns the `AppException` type,
   the `ErrorType` taxonomy, the `QDebug` stream operator that names an
   `ErrorType`, and `errorMessageHandler`, which converts Qt log calls into
   stderr lines, message boxes, and (for Critical/Fatal) thrown exceptions.

```
                         qInstallMessageHandler(errorMessageHandler)
                                        |
   qDebug/qInfo/qWarning/qCritical/qFatal  ->  errorMessageHandler()
                                        |             |
                              format + _DEBUG log   showMessage()/ERROR_MESSAGE
                                        |             |
                    Critical/Fatal: throw AppException  QMessageBox::info/warn/critical
                                        |
   main() try { MainWindow window; window.show(); app->exec(); }
        catch (AppException&)  -> cerr + QMessageBox::critical + return EXIT_FAILURE
        catch (QException&)    -> cerr + QMessageBox::critical + return EXIT_FAILURE
        catch (std::exception&)-> cerr + QMessageBox::critical + return EXIT_FAILURE
        catch (...)            -> cerr + QMessageBox::critical + return EXIT_FAILURE
```

## Data structures & models

`ErrorType` (`src/Exceptions/Exceptions.h:21-25`), the error taxonomy:

```cpp
/// XXZZ: XX is category, ZZ is subcategory
enum class ErrorType
{
    Invalid = 0,
    General = 1
};
```

The "XXZZ" convention encodes a 2-digit category and 2-digit subcategory into a
single 4-digit code. Only two members exist today. Values are plain decimal
literals with no leading zeros: a leading-zero literal (e.g. `0008`) is parsed as
**octal** and fails to compile for digits 8-9 (see Gotchas), so both the enum and
the C1 contract keep the literals zero-free.

`AppException` (`src/Exceptions/Exceptions.h:29-53`), the project exception:

```cpp
class AppException : public QException
{
public:
    AppException(const char* msg, ErrorType errorType = ErrorType::General);
    // copy + move defaulted; virtual ~AppException() = default;
    void raise()          const override;   // throw *this;
    AppException* clone() const override;   // new AppException(*this);
    const char* what()    const noexcept override; // returns msg_.c_str()
    const ErrorType errorType;              // public, const, set at construction
private:
    std::string msg_;
};
```

`raise()`/`clone()` implement the `QException` contract that lets the exception
survive being propagated across Qt's `QtConcurrent` boundaries. `errorType` is a
`public const` member fixed at construction.

`MainWindow` (`src/mainwindow.h:28-99`) - a `QMainWindow` subclass holding a
`Ui::MainWindow* ui`. The class also declares a large set of **Doxygen-demo**
members that are not part of any real model: nested `class Point`, `typedef int
someType`, `func1/2/3`, `static_func1/2/3`, `static_var1/2/3`, `var1/2/3`,
`slot`, `signal(int)`, `privateSlot`, plus free `struct someStruct`, namespaces
`myOwnNamespace`/`myOwnNamespace2`, and a `DifferentWindow : public MainWindow`.
The `Ui::MainWindow` type is generated by UIC from `mainwindow.ui`.

The `.ui` model (`src/mainwindow.ui`): a `QMainWindow` named `MainWindow`,
geometry `709x550`, `minimumSize` `600x550`, 11pt font, a `centralWidget`
(min `600x500`) with an empty `QVBoxLayout verticalLayout`, a `menuBar`, and a
`statusBar`. No widgets, no connections.

## Control & data flow

Primary path - `main()` (`src/main.cpp:8-75`):

1. Define `showExceptionMessageBox` lambda (`:10`) and `returnCode = -1` (`:14`).
2. **QApplication bootstrap** in its own `try` (`:18-40`):
   `app = std::make_unique<QApplication>(argc, argv)` (`:20`), then
   `setOrganizationName("QtTemplate")` and `setApplicationName("qt6-template")`
   (`:21-22`). Its three catches (`QException`, `std::exception`, `...`) log to
   `stderr` and **`return EXIT_FAILURE`** - deliberately no message box, because a
   `QMessageBox` needs a live `QApplication` that just failed to construct.
3. **Event-loop block** in a second `try` (`:42-84`):
   - `qInstallMessageHandler(errorMessageHandler)` (`:44`) - from here on every
     Qt log call routes through the funnel.
   - **`--self-test` branch** (`:46-52`): if `app->arguments()` contains
     `--self-test`, construct + `show()` `MainWindow`, schedule
     `QTimer::singleShot(0, app.get(), &QCoreApplication::quit)`, and
     `return app->exec()` (0 on the happy path). Offscreen-safe smoke path CI runs.
   - `MainWindow window;` (`:53`) -> `MainWindow::MainWindow` runs
     `new Ui::MainWindow`, `ui->setupUi(this)`, sets window icon
     `":/resource/icon/icon_32x32.png"` and title "Qt Template"
     (`mainwindow.cpp:8-16`). It also constructs an unused
     `boost::multiprecision::int1024_t bigInt` (a link-smoke line).
   - `window.show()` (`:54`).
   - `returnCode = app->exec()` (`:55`) - blocks in the event loop.
4. **Normal exit**: `exec()` returns, control reaches the no-op
   `boost::filesystem::recursive_directory_iterator it;` (`:85`, another link
   smoke line), then `return returnCode` (`:86`).
5. **Error branch**: any exception out of step 3 hits the ladder
   (`AppException` -> `QException` -> `std::exception` -> `...`, `:57-84`),
   which logs `[Critical] ...` to `stderr`, calls `showExceptionMessageBox(...)`,
   and **`return EXIT_FAILURE`**. Each catch returns instead of rethrowing, so
   `main` exits with a failure code rather than terminating via `std::terminate`.

Logging path - `errorMessageHandler` (`src/Exceptions/Exceptions.cpp:41-124`):

1. Map `QtMsgType` -> category string (`Debug`/`Info`/`Warning`/`Critical`/
   `Fatal`; `default` falls through to `Info`) (`:44-62`).
2. Trim `context.file` to its basename and build
   `[file:line][function]\n<msg>` then prefix `[category] ` (`:63-67`).
3. `_DEBUG`-gated log (`:68-73`): if `_DEBUG` is defined, print everything to
   `stderr`; otherwise print everything **except** `Debug` messages.
4. Define `showMessage` lambda (`:74-104`) that, in Widgets mode, calls
   `QMessageBox::information` / `warning` / `critical` by type.
5. Dispatch (`:106-123`):
   - `Info`/`Warning` -> `showMessage()` (box only).
   - `Critical`/`Fatal` -> `ERROR_MESSAGE(...)` (== `showMessage()`) **then
     `throw AppException(messageWithCategory...)`**.
   - `Debug`/`default` -> nothing (already logged in step 3 when `_DEBUG`).

## Public API / contracts
Downstream domains may rely on:

- **CMake targets**: executable `qt6-template` and static library
  `qt6-template_LIB`, both built from the same `SOURCE_FILES`
  (`CMakeLists.txt`). Tests link the library, not the executable. The alias
  `qt6-template::qt6-template` maps to the executable
  (`CMakeLists.txt`, "Provide alias to library").
- **`AppException(const char* msg, ErrorType = ErrorType::General)`** - the
  canonical app exception; overrides `what()`, `raise()`, `clone()`; exposes
  `public const ErrorType errorType`. Constructor argument order is
  `(msg, errorType)`.
- **`enum class ErrorType`** with the documented "XXZZ" category/subcategory
  contract (`Exceptions.h:20-25`).
- **`void errorMessageHandler(QtMsgType, const QMessageLogContext&, const QString&)`**
  - the handler to hand to `qInstallMessageHandler`. Contract: Critical/Fatal
  logs are converted into thrown `AppException`s.
- **`QDebug operator<<(QDebug, const ErrorType&)`** - lets callers write
  `qCritical() << ErrorType::General << "message"`.
- **`ERROR_MESSAGE(msg)` macro** - Widgets build shows a message box (note it
  ignores its argument; see Gotchas).
- **Qt conventions guarantee**: any header with `Q_OBJECT` is MOC'd
  automatically; any `src/**/*.ui` yields `ui_<name>.h`; any `.qrc`/QML is
  compiled - because `CMAKE_AUTOMOC`/`AUTOUIC`/`AUTORCC` are `ON`
  (`CMakeLists.txt`).
- **Test-add contract**: dropping a `.cpp` with `QTEST_MAIN` into `test/`
  auto-registers a CTest test (`cmake/Sources.cmake` globs `test/*.cpp`;
  `test/CMakeLists.txt` builds one executable + `add_test` per file).

## Dependencies
Inbound (callers into this domain):
- `test/testTest.cpp:2,15` includes `mainwindow.h` and constructs
  `new MainWindow(nullptr)` - the only test that drives a domain symbol
  directly. `test/gslLinkTest.cpp` and `test/integrationSmokeTest.cpp` link the
  library but exercise Qt/Boost/GSL, not domain symbols.
- The build domain instantiates the `qt6-template` / `qt6-template_LIB` targets
  from these sources.

Outbound (what this domain depends on):
- **Qt6**: `Core`, `Gui`, `Widgets` (`cmake/Modules.cmake`); classes
  `QApplication`, `QMainWindow`, `QMessageBox`, `QException`, `QDebug`,
  `QString`, `QIcon`, `QCoreApplication`, `qInstallMessageHandler`.
- **Boost**: `filesystem` component (`main.cpp:4`, link-smoke) and header-only
  `multiprecision` (`mainwindow.cpp:4`, link-smoke).
- **ms-gsl** (`Microsoft.GSL::GSL`) - linked to all targets but only used by
  tests (`gslLinkTest.cpp`, `integrationSmokeTest.cpp`), not by domain source.
- **Generated headers**: `ui_mainwindow.h` (UIC), `*.moc` and
  `mocs_compilation_*.cpp` (MOC).
- **Standard library**: `<iostream>` (`std::cerr`), `<string>`,
  `<memory>` (`std::unique_ptr`).

## Invariants & assumptions
- **ErrorType / string-map sync**: the string mapping lives in the `switch` inside
  `operator<<(QDebug, const ErrorType&)` (`Exceptions.cpp:27-39`), which only handles
  `ErrorType::General` and sends everything else to the `default`
  ("[Unknown Error: N]"). The real invariant to honor when adding an `ErrorType`
  is: **add a matching `case` to that switch.** `CLAUDE.md` and
  `.github/copilot-instructions.md` now document exactly this - the phantom
  `ErrorTypeStr[]` array reference has been purged from both.
- **XXZZ octal trap**: enumerator values are written as plain decimal literals
  (`0`, `1`) with no leading zeros, honoring the C1 contract. New codes must stay
  zero-free: a leading-zero literal with digit `8`/`9` (e.g. `0108` or `0019`) is
  parsed as octal and fails to compile.
- **Handler installed before any log**: `qInstallMessageHandler` runs at
  `main.cpp:40`, before `MainWindow` construction, so any Qt log during startup
  is funneled. Logs emitted before line 40 use Qt's default handler.
- **QApplication before any QWidget/QMessageBox**: the message-box lambdas and
  `MainWindow` assume a live `QApplication`; the first catch block intentionally
  does not show a box for exactly this reason.
- **Catch ordering**: because `AppException : QException : std::exception`, the
  ladder must list most-derived first (`AppException`, then `QException`, then
  `std::exception`, then `...`). Reordering would shadow subtypes.
- **Two targets, one `main()`**: the static library `qt6-template_LIB` is built
  from the same `SOURCE_FILES`, so it contains `main.cpp`'s `main()`. Test
  executables define their own `main()` via `QTEST_MAIN`, so the linker never
  pulls `main.o` from the archive (its `main` symbol is already resolved) - no
  duplicate-symbol error. This only works because static-archive extraction is
  demand-driven.

## Error handling & edge cases
- **Two-stage guarding**: QApplication construction (`main.cpp:16-36`) and the
  event loop (`:38-72`) have separate `try` blocks with different recovery: the
  first cannot surface UI, the second can.
- **Log-to-exception bridge**: `qCritical`/`qFatal` do not just log - they throw
  `AppException` from inside `errorMessageHandler` (`Exceptions.cpp:117`). This
  means a critical log emitted anywhere (including deep in Qt callbacks) unwinds
  to `main`'s ladder.
- **`qFatal` no longer aborts**: because the handler throws before returning,
  Qt's usual post-`qFatal` `abort()` is preempted by exception unwinding.
- **Every catch returns `EXIT_FAILURE`**: the ladder surfaces a box then
  `return EXIT_FAILURE`, so `main()` exits with a failure code instead of
  terminating via `std::terminate`. There is still no "show error and keep
  running" path - a critical log ends the process, but now with a clean exit code.
- **Unknown `ErrorType`**: `operator<<` default branch prints
  `[Unknown Error: <int>]` instead of a name (`Exceptions.cpp:34-36`) -
  graceful, not a crash.
- **Empty message / null parent**: message boxes use `nullptr` parent
  throughout, so they are top-level and parentless (acceptable but not tied to
  the main window).

## Concurrency / async / lifecycle
- Single-threaded Qt Widgets app: one `QApplication` event loop
  (`app->exec()`), no explicit threads.
- **Lifecycle**: `QApplication` is heap-owned via `std::unique_ptr` and outlives
  `MainWindow` (declared on the stack inside the same `try`, destroyed when the
  block unwinds). `MainWindow` owns `ui` via raw pointer, freed in the dtor.
- **Async boundary / hazard**: throwing an exception out of `errorMessageHandler`
  while inside `app->exec()` crosses the Qt event-dispatch machinery. Exceptions
  propagating through Qt's event loop are only conditionally supported by Qt and
  are a known fragile pattern (see Gotchas).
- `AppException::raise()`/`clone()` exist specifically so the exception can be
  marshaled across `QtConcurrent`/thread boundaries, though nothing in this
  template currently uses concurrency.

## Performance
N/A for the hot path - this is a template skeleton with an empty window and no
compute. Minor notes: `errorMessageHandler` allocates several `QString`s and a
`std::to_string` per log call, but logging is not a hot path. The
`int1024_t bigInt` and `recursive_directory_iterator it` are default-constructed
no-ops with negligible cost, present only to force linkage.

## Gotchas & footguns
- **No `ErrorTypeStr[]` array**: there is no lookup array anywhere - a search for
  `ErrorTypeStr` now returns zero hits (the stale references in `CLAUDE.md` and
  `.github/copilot-instructions.md` have been purged). The live mapping is the
  `switch` in `operator<<` (`Exceptions.cpp:27-39`); extend the switch.
- **`ERROR_MESSAGE(msg)` ignores its argument**: `#define ERROR_MESSAGE(msg)
  showMessage()` (`Exceptions.h:17`) drops the token entirely, so at
  `Exceptions.cpp:116` the `messageWithCategory.toLocal8Bit().data()` argument is
  never evaluated. The box text comes from the lambda's captured
  `messageContent`, not from what you pass. Confusing but harmless (no side
  effects in the discarded expression).
- **Octal enum literals**: see Invariants - `ErrorType` values like `0308` or
  `0019` are octal and can fail to compile or silently mean the wrong number.
- **Exceptions thrown through the Qt event loop**: the whole "critical log ->
  throw" design relies on the exception traversing `app->exec()`. This is
  fragile across Qt versions/platforms and is a classic footgun; treat with care
  before building real error flows on it.
- **`main()` lives in the static library**: editing `main.cpp` changes both the
  executable and `qt6-template_LIB`. It works today only because tests supply
  their own `QTEST_MAIN` `main`; a test that both links the lib and omits
  `QTEST_MAIN` could pull `main.o`.
- **Doxygen-demo noise in `mainwindow.h`**: `someStruct`, `Point`, `someType`,
  `func1/2/3`, `static_func1/2/3`, `static_var1/2/3`, `var1/2/3`, `slot`,
  `signal`, `privateSlot`, `myOwnNamespace*`, and `DifferentWindow` are
  documentation examples, not app logic. Do not build features on them.
- **Undefined `static_var1/2/3`**: declared in the header but defined nowhere;
  ODR-using any of them yields a link error. They exist only for Doxygen.
- **Abandoned QML/Qt-Quick path (known dead end)**: `main.cpp:77-136` keeps an
  entire commented-out `QGuiApplication`+`QQmlApplicationEngine` `main`, and
  `Exceptions.*` keeps commented QML branches (`AppException::exceptionMessage`,
  a QML "showMessage" invoke). The project deliberately ships the **Widgets**
  path; the QML path is a template alternative that was never activated. The
  `src/qml/` directory contains only a zero-byte placeholder literally named
  `Here you should place your qml files`. The commented
  `throw AppException(msg, ErrorType::General)` at `Exceptions.cpp:81` is now in the
  correct `(msg, ErrorType)` order for the real constructor
  `AppException(const char* msg, ErrorType)` - the earlier swapped-arg bug has been
  fixed, so the block would compile if revived.
- **`befriendedFunction` takes `MainWindow` by value**: `QObject` is
  non-copyable, so the definition compiles only because it is never called;
  calling it would fail to compile. It is a `friend`-keyword Doxygen demo.
- **Two link-smoke lines in production code**:
  `boost::filesystem::recursive_directory_iterator it;` (`main.cpp:73`) and
  `boost::multiprecision::int1024_t bigInt;` (`mainwindow.cpp:12`) are
  unused locals whose sole purpose is to force Boost linkage. Do not "clean them
  up" without also adjusting the dependency wiring/tests they stand in for.

## Tech debt & smells
- Large blocks of dead commented code: `main.cpp:89-148` (QML `main`),
  `Exceptions.h:9-14,47-48`, `Exceptions.cpp:3-4,76-84` (QML branches).
- `ERROR_MESSAGE(msg)` macro with an ignored parameter (`Exceptions.h:17`) - an
  easy source of misreading.
- Unused link-smoke locals: `main.cpp:73`, `mainwindow.cpp:12`.
- Doxygen-demo bloat in `mainwindow.h:8-104` mixed into a real header.
- `errorMessageHandler` builds a `QString` from `std::to_string(...).c_str()`
  (`Exceptions.cpp:65`) - a needless round-trip through the C++ standard string.
- The `throw`-from-message-handler design (`Exceptions.cpp:117`) is inherently
  fragile (see Gotchas) and couples logging to control flow.

## Test surface
Framework: **Qt Test** (`Qt6::Test`), each file a standalone executable via
`QTEST_MAIN`, discovered by CTest. Tests link `qt6-template_LIB`
(`test/CMakeLists.txt` selects `${PROJECT}_LIB` when `_BUILD_EXECUTABLE` is ON).

- `test/errorHandlingTest.cpp` - unit tests for the error funnel: invoking
  `errorMessageHandler(QtCriticalMsg, ...)` directly throws a catchable
  `AppException` with `what()`/`errorType` intact; `qWarning`/`qInfo`/`qDebug`
  routed through the handler do not throw; and `AppException`'s
  `what`/`clone`/`raise`/`errorType` are checked directly.
- `test/testTest.cpp` - constructs `new MainWindow(nullptr)`, checks
  `QString::toUpper`, and touches `boost::filesystem`. The only test that
  exercises a domain symbol (`MainWindow`).
- `test/gslLinkTest.cpp` - `gsl::not_null` smoke (GSL linkage).
- `test/integrationSmokeTest.cpp` - Qt + Boost (`BOOST_VERSION >= 109100`) + GSL
  linked together.

Exact commands (from `CLAUDE.md` / Makefile; require a display or offscreen):

```bash
# configure + build (Release)
cmake . -G Ninja -B build -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# run the suite headless
cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -VV

# or via the Makefile entrypoint (sets QT_QPA_PLATFORM=offscreen)
make test
```

`test/errorHandlingTest.cpp` now covers the Critical/Fatal `throw AppException`
funnel, the non-throwing Info/Warning/Debug paths, and
`AppException::what`/`raise`/`clone`/`errorType`. Still untested:
`errorMessageHandler`'s log formatting and the `_DEBUG` gate,
`operator<<(QDebug, ErrorType)`'s string output, the `main()` catch ladder
end-to-end, and the `MainWindow` UI (icon/title/`setupUi`). No test drives the QML
path (there is no QML).

## Extension points
- **Add an error category**: extend `enum class ErrorType` (`Exceptions.h:21`)
  using the XXZZ format (mind the octal-literal trap), then add a matching
  `case` to `operator<<` (`Exceptions.cpp:27-39`). This is the real "sync"
  step; there is no `ErrorTypeStr[]` array.
- **Throw an app error**: `throw AppException("message", ErrorType::General);`
  or emit `qCritical() << ErrorType::General << "message";` to route through the
  funnel.
- **Add UI**: edit `mainwindow.ui` in Qt Designer (AUTOUIC regenerates
  `ui_mainwindow.h`); declare `Q_OBJECT` slots/signals in `mainwindow.h`
  (AUTOMOC handles MOC); wire widgets in `MainWindow::MainWindow`.
- **Add a test**: drop a `test/<name>.cpp` with a `Q_OBJECT` fixture,
  `QTEST_MAIN`, and `#include "<name>.moc"`; `cmake/Sources.cmake` globs it and
  `test/CMakeLists.txt` auto-creates the executable + `add_test`.
- **Revive QML / Qt Quick**: uncomment the `main.cpp:89-148` block and the QML
  branches in `Exceptions.*`, place `.qml` files under `src/qml/` (replacing the
  placeholder), and enable the `Quick` component so `qt6-template_QT_QUICK`
  turns on the `qt_add_qml_module` path in `CMakeLists.txt`. (The earlier
  arg-order bug at `Exceptions.cpp:81` has already been fixed.)
