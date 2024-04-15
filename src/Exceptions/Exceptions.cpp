#include "Exceptions.h"

//QML
//QObject* AppException::exceptionMessage = nullptr;

AppException::AppException(const char* msg__, ErrorType errorType__)
	: errorType(errorType__),
      msg_(msg__)
{
}

void AppException::raise() const
{
	throw *this;
}

AppException* AppException::clone() const
{
	return new AppException(*this);
}

const char* AppException::what() const noexcept
{
    return msg_.c_str();
}

QDebug operator<<(QDebug d, const ErrorType& errorType)
{
	d << ErrorTypeStr[static_cast<int>(errorType)];
	return d;
}

void errorMessageHandler(QtMsgType type, const QMessageLogContext& context, const QString& msg)
{
    QString category = QStringLiteral("Invalid");
    switch (type)
    {
    case QtDebugMsg:
        category = QStringLiteral("Debug");
        break;
    default:
    case QtInfoMsg:
        category = QStringLiteral("Info");
        break;
    case QtWarningMsg:
        category = QStringLiteral("Warning");
        break;
    case QtCriticalMsg:
        category = QStringLiteral("Critical");
        break;
    case QtFatalMsg:
        category = QStringLiteral("Fatal");
        break;
    }
    QString file{ context.file };
    file = file.mid(qMax(file.lastIndexOf('/'), file.lastIndexOf('\\')) + 1);
    const QString message = '[' + category + "] [" + file + ':' + std::to_string(context.line).c_str() + "] [" + context.function + "]\n" + msg;
#ifdef _DEBUG
    std::cerr << message.toLocal8Bit().data() << std::endl;
#else
    if (category != QStringLiteral("Debug"))
        std::cerr << message.toLocal8Bit().data() << std::endl;
#endif
    auto showMessage = [&]()
    {
        //QML
        /* {
            if (AppException::exceptionMessage && !QMetaObject::invokeMethod(AppException::exceptionMessage, "showMessage", Q_ARG(QString, message)))
            {
                constexpr const char* msg = "[Critical] Could not display the exception message in QML: failed to invoke Dialog's \"showMessage\" method (missing? wrong signature?). Possibly corrupt \"Main.qml\" file";
                ERROR_MESSAGE(msg);
                throw AppException(ErrorType::General, msg);
            }
        }*/
        //Widgets
        {
            QString msg = message.mid(message.indexOf(']') + 2);
            switch (type)
            {
            case QtInfoMsg:
                QMessageBox::information(nullptr, category, msg);
                break;
            case QtWarningMsg:
                QMessageBox::warning(nullptr, category, msg);
                break;
            case QtCriticalMsg:
            case QtFatalMsg:
                QMessageBox::critical(nullptr, category, msg);
                break;
            case QtDebugMsg:
            default:
                break;
            }
        }
    };

    switch (type)
    {
    case QtInfoMsg:
    case QtWarningMsg:
        //QMessageBoxes won't display when used with Qt Quick, so you can remove this line, if you use it
        showMessage();
    break;

    case QtCriticalMsg:
    case QtFatalMsg:
        ERROR_MESSAGE(message.toLocal8Bit().data());
        throw AppException(message.toLocal8Bit().data());
    break;

    case QtDebugMsg:
    default:
        break;
    }
}