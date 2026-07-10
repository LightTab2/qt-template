#include "mainwindow.h"

#include <QApplication>
#include <QTimer>
#include <boost/filesystem.hpp>

#include <cstdlib>

#include "Exceptions/Exceptions.h"

int main(int argc, char* argv[])
{
    auto showExceptionMessageBox = [](const QString& message) {
        QMessageBox::critical(nullptr, "Critical", message);
    };
    int returnCode = -1;
    std::unique_ptr<QApplication> app = nullptr;
    try
    {
        app = std::make_unique<QApplication>(argc, argv);
        QCoreApplication::setOrganizationName("QtTemplate");
        QCoreApplication::setApplicationName("qt6-template");
    }
    catch (QException& ex)
    {
        std::cerr << "[Critical] Couldn't create QApplication:\n" << ex.what();
        return EXIT_FAILURE;
    }
    catch (std::exception& ex)
    {
        std::cerr << "[Critical] Couldn't create QApplication:\n" << ex.what();
        return EXIT_FAILURE;
    }
    catch (...)
    {
        std::cerr << "[Critical] Couldn't create QApplication:\nUnknown error!";
        return EXIT_FAILURE;
    }

    try
    {
        qInstallMessageHandler(errorMessageHandler);
        // --self-test: headless smoke - construct, show, quit after one event-loop pass
        if (app->arguments().contains(QStringLiteral("--self-test")))
        {
            MainWindow window;
            window.show();
            QTimer::singleShot(0, app.get(), &QCoreApplication::quit);
            return app->exec();
        }
        MainWindow window;
        window.show();
        returnCode = app->exec();
    }
    catch (AppException& ex)
    {
        std::cerr << "[Critical] " << ex.what();
        showExceptionMessageBox(ex.what());
        return EXIT_FAILURE;
    }
    catch (QException& ex)
    {
        std::cerr << "[Critical] Unidentified \"QException\" has occurred: " << ex.what();
        QString msg = "Unidentified \"QException\" has occurred:\n";
        msg += ex.what();
        showExceptionMessageBox(msg);
        return EXIT_FAILURE;
    }
    catch (std::exception& ex)
    {
        std::cerr << "[Critical] Unidentified \"std::exception\" has occurred: " << ex.what();
        QString msg = "Unidentified \"std::exception\" has occurred:\n";
        msg += ex.what();
        showExceptionMessageBox(msg);
        return EXIT_FAILURE;
    }
    catch (...)
    {
        std::cerr << "[Critical] Unidentified exception has occurred\n";
        showExceptionMessageBox("Unidentified exception has occurred");
        return EXIT_FAILURE;
    }
    boost::filesystem::recursive_directory_iterator it;
    return returnCode;
}

/* Qt Quick main
int main(int argc, char* argv[])
{
    int returnCode = -1;
    try
    {
        qInstallMessageHandler(errorMessageHandler);
        QGuiApplication app(argc, argv);
        QQmlApplicationEngine engine;
        engine.load(QUrl(QStringLiteral("qrc:/qt/qml/qt_template/Main.qml")));
        if (engine.rootObjects().isEmpty())
            qCritical() << ErrorType::General << "Couldn't load \"Main.qml\"";

        QObject* rootObject = engine.rootObjects()[0];
        MainWindow* mainWindow = qobject_cast<MainWindow*>(rootObject);
        if (!mainWindow)
            qCritical() << ErrorType::General << "Problem loading the QML file: Root object is not a MainWindow. Possibly corrupt \"Main.qml\" file";

        app.setWindowIcon(QIcon(QStringLiteral(":/qt/qml/qt_template/icon/icon_32x32.png")));

        // Recommendation: create a Dialog in your QML for debug/info messages
        // Connect Dialog that is within our main object, so it will be displayed if an exception happens

        //AppException::exceptionMessage = mainWindow->findChild<QObject*>(QStringLiteral("exceptionMessage"));
        //if (!AppException::exceptionMessage)
        //    qCritical() << ErrorType::General << "Problem loading the QML file: Couldn't find the Dialog responsible for displaying exception messages. Possibly corrupt \"Main.qml\" file";

        returnCode = app.exec();
    }
    catch (AppException& ex)
    {
        std::cerr << "[Critical] " << ex.what();
        ERROR_MESSAGE(ex.what());
        throw;
    }
    catch (QException& ex)
    {
        std::cerr << "[Critical] Unidentified \"QException\" has occurred: " << ex.what();
        std::string msg = "Unidentified \"QException\" has occurred:\n";
        msg += ex.what();
        ERROR_MESSAGE(msg.c_str());
        throw;
    }
    catch (std::exception& ex)
    {
        std::cerr << "[Critical] Unidentified \"std::exception\" has occurred: " << ex.what();
        std::string msg = "Unidentified \"std::exception\" has occurred:\n";
        msg += ex.what();
        ERROR_MESSAGE(msg.c_str());
        throw;
    }
    catch (...)
    {
        std::cerr << "[Critical] Unidentified exception has occurred\n";
        ERROR_MESSAGE("Unidentified exception has occurred");
        throw;
    }
    return returnCode;
}
*/

void befriendedFunction(MainWindow win)
{
    win.func2(12);
}