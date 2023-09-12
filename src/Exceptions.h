#pragma once

#include <QDebug>
#include <QException>
#include <QString>

#include <iostream>

//QML
//#include <QtQuick>
//#define ERROR_MESSAGE(msg)
//#ifdef WIN32
//#define ERROR_MESSAGE(msg) MessageBoxA(NULL, msg, "Error", MB_OK | MB_ICONERROR)
//#endif

//Widgets
#define ERROR_MESSAGE(msg) showMessage()
#include <QMessageBox>

enum class ErrorType
{
	General,
	Unidentified
};

constexpr char const* const ErrorTypeStr[]
{
	"[General]",
	"[Unidentified]"
};

/// An exception class to distinguish between QExceptions thrown from Qt library and this project
///
class AppException final : public QException
{
public:
	// Constructor
	AppException(const char* msg, ErrorType errorType = ErrorType::General);
	// Allow copy
	AppException(const AppException&)            = default;
	AppException& operator=(const AppException&) = default; //cpp20
	// Allow move
	AppException(AppException&&)            noexcept = default;
	AppException& operator=(AppException&&) noexcept = default; //cpp20
	// Destructor
	~AppException() = default;

	void raise() const override;
	AppException* clone() const override;
	const char* what() const override;

	//QML
	//static QObject* exceptionMessage;
	
	const ErrorType errorType;
private:
	std::string msg_;
};


/// Along with \ref errorMessageHandler(QtMsgType,const QMessageLogContext&,const QString&) allows to use exception system and/or logging system in a more transparent way.
/// 
/// Instead of throwing exceptions use:
/// - `qDebug() << [ErrorType] << [message]` for information that should be written in a log only when debugging is enabled
/// - `qInfo() << [ErrorType] << [message]` for information that should be written in a log
/// - `qWarn() << [ErrorType] << [message]` for information that should be displayed as a warning to the user
/// - `qCritical() << [ErrorType] << [message]` for exceptions
/// - `qFatal() << [ErrorType] << [message]` for exceptions that cannot be recovered from
QDebug operator<<(QDebug logger, const ErrorType& errorType);

/// Along with \ref operator<<(QDebug, const ErrorType&) allows to use exception system and/or logging system in a more transparent way.
/// 
/// Instead of throwing exceptions use:
/// - `qDebug() << [ErrorType] << [message]` for information that should be written in a log only when debugging is enabled
/// - `qInfo() << [ErrorType] << [message]` for information that should be written in a log
/// - `qWarn() << [ErrorType] << [message]` for information that should be displayed as a warning to the user
/// - `qCritical() << [ErrorType] << [message]` for exceptions
/// - `qFatal() << [ErrorType] << [message]` for exceptions that cannot be recovered from
void errorMessageHandler(QtMsgType type, const QMessageLogContext& context, const QString& msg);