#include "mainwindow.h"

#include <iostream>

#include <QApplication>
#include <QException>
#include <boost/filesystem.hpp>

int main(int argc, char *argv[])
{
    boost::filesystem::recursive_directory_iterator it;
    int returnCode = -1;
    try
    {
        QApplication a(argc, argv);
        MainWindow w;
        w.show();
        returnCode = a.exec();
    }
    /*catch (AppException& ex)
    {
        std::cerr << ex.what();
#ifdef WIN32
        ERROR_MESSAGE(ex.what());
#endif
    }*/
    catch (QException& ex)
    {
        std::cerr << "Unidentified \"QException\" has occurred: " << ex.what();
#ifdef WIN32
        std::string msg = "Unidentified \"QException\" has occurred:\n";
        msg += ex.what();
        //ERROR_MESSAGE(msg.c_str());
#endif
    }
    catch (std::exception& ex)
    {
        std::cerr << "Unidentified \"std::exception\" has occurred: " << ex.what();
#ifdef WIN32
        std::string msg = "Unidentified \"std::exception\" has occurred:\n";
        msg += ex.what();
        //ERROR_MESSAGE(msg.c_str());
#endif
    }
    catch (...)
    {
        std::cerr << "Unidentified exception has occurred\n";
#ifdef WIN32
        //ERROR_MESSAGE("Unidentified exception has occurred\n");
#endif
    }
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
        std::cerr << ex.what();
#ifdef WIN32
        ERROR_MESSAGE(ex.what());
#endif
    }
    catch (QException& ex)
    {
        std::cerr << "Unidentified \"QException\" has occurred: " << ex.what();
#ifdef WIN32
        std::string msg = "Unidentified \"QException\" has occurred:\n";
        msg += ex.what();
        ERROR_MESSAGE(msg.c_str());
#endif
    }
    catch (std::exception& ex)
    {
        std::cerr << "Unidentified \"std::exception\" has occurred: " << ex.what();
#ifdef WIN32
        std::string msg = "Unidentified \"std::exception\" has occurred:\n";
        msg += ex.what();
        ERROR_MESSAGE(msg.c_str());
#endif
    }
    catch (...)
    {
        std::cerr << "Unidentified exception has occurred\n";
#ifdef WIN32
        ERROR_MESSAGE("Unidentified exception has occurred\n");
#endif
    }
    return returnCode;
}
*/

void befriendedFunction(MainWindow win)
{
    win.func2(12);
}