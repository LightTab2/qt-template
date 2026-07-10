#include <QtTest>

#include <QApplication>
#include <QMessageBox>
#include <QTimer>

#include <memory>

#include "Exceptions/Exceptions.h"

/// \brief Repeatedly closes the innermost modal QMessageBox the handler opens, firing inside that
/// box's own modal event loop, until the slot ends. The returned timer stops when it goes out of
/// scope at the slot's end.
///
/// A repeating timer (not a single shot) is required: under the offscreen platform, showing a box
/// emits qWarning("This plugin does not support propagateSizeHints()"), which the installed handler
/// turns into a second, nested box; a single shot gets consumed inside that nested loop and nothing
/// is left to close the outer box, deadlocking the test. Closing ONLY
/// QApplication::activeModalWidget() (never every top-level box) is equally load-bearing: hiding
/// the outer box before its exec() loop starts leaves that loop unable to exit - every dismissal
/// path short-circuits in QDialog::setVisible(false) once the box is already hidden.
///
/// closedCount is incremented once per box actually closed, so a caller can assert the modal path
/// really engaged (rather than only that nothing threw).
static std::unique_ptr<QTimer> startMessageBoxAutoClose(int& closedCount)
{
    auto timer = std::make_unique<QTimer>();
    timer->setInterval(100);
    QObject::connect(timer.get(), &QTimer::timeout, [&closedCount]() {
        if (auto* box = qobject_cast<QMessageBox*>(QApplication::activeModalWidget()))
        {
            box->close();
            ++closedCount;
        }
    });
    timer->start();
    return timer;
}

/// \brief Unit tests for AppException and the errorMessageHandler funnel.
class ErrorHandlingTest : public QObject
{
    Q_OBJECT

  private slots:
    void init();    ///< \brief Installs errorMessageHandler fresh before every test.
    void cleanup(); ///< \brief Restores the default message handler after every test.
    void appExceptionPreservesFields();
    void appExceptionCloneAndRaise();
    void criticalThrowsAppException();
    void warningDoesNotThrow();
    void infoDoesNotThrow();
    void debugDoesNotThrow();
};

void ErrorHandlingTest::init()
{
    qInstallMessageHandler(errorMessageHandler);
}

void ErrorHandlingTest::cleanup()
{
    qInstallMessageHandler(nullptr);
}

/// \brief AppException keeps its message and errorType, including the ErrorType::General default
/// argument.
void ErrorHandlingTest::appExceptionPreservesFields()
{
    const AppException ex("boom", ErrorType::General);
    QCOMPARE(QString(ex.what()), QString("boom"));
    QVERIFY(ex.errorType == ErrorType::General);

    const AppException defaulted("x");
    QVERIFY(defaulted.errorType == ErrorType::General);
}

/// \brief clone() copies message and errorType intact; raise() throws the exception itself.
void ErrorHandlingTest::appExceptionCloneAndRaise()
{
    const AppException ex("boom", ErrorType::General);
    const std::unique_ptr<AppException> copy(ex.clone());
    QCOMPARE(QString(copy->what()), QString("boom"));
    QVERIFY(copy->errorType == ErrorType::General);
    QVERIFY_THROWS_EXCEPTION(AppException, ex.raise());
}

/// \brief Invoking errorMessageHandler(QtCriticalMsg, ...) directly throws a catchable AppException
/// with the original message embedded in what() and errorType intact.
///
/// Direct invocation is the mandated proof idiom: stream-style qCritical() would throw inside the
/// implicitly noexcept ~QDebug() and std::terminate the whole binary instead of being caught.
void ErrorHandlingTest::criticalThrowsAppException()
{
    int closed = 0;
    const auto autoClose = startMessageBoxAutoClose(closed);
    bool caught = false;
    try
    {
        const QMessageLogContext ctx("errorHandlingTest.cpp", 0, "criticalThrowsAppException",
                                     "default");
        errorMessageHandler(QtCriticalMsg, ctx, QStringLiteral("test critical"));
    }
    catch (const AppException& ex)
    {
        caught = true;
        QVERIFY(QString(ex.what()).contains("test critical"));
        QVERIFY(ex.errorType == ErrorType::General);
    }
    QVERIFY(caught);
    QVERIFY(closed >= 1); // the modal critical box was actually shown and auto-closed
}

/// \brief qWarning routed through the handler opens a box (auto-closed) and never throws.
void ErrorHandlingTest::warningDoesNotThrow()
{
    int closed = 0;
    const auto autoClose = startMessageBoxAutoClose(closed);
    qWarning() << ErrorType::General << "w";
    QVERIFY(closed >= 1); // the warning routed through the handler and opened a box
}

/// \brief qInfo routed through the handler opens a box (auto-closed) and never throws.
void ErrorHandlingTest::infoDoesNotThrow()
{
    int closed = 0;
    const auto autoClose = startMessageBoxAutoClose(closed);
    qInfo() << ErrorType::General << "i";
    QVERIFY(closed >= 1); // the info routed through the handler and opened a box
}

/// \brief qDebug routed through the handler opens no box and never throws.
void ErrorHandlingTest::debugDoesNotThrow()
{
    qDebug() << ErrorType::General << "d";
    QVERIFY(true);
}

QTEST_MAIN(ErrorHandlingTest)
#include "errorHandlingTest.moc"
