#include <QTest>

#include <boost/filesystem.hpp>

#include "mainwindow.h"

class TestQString : public QObject
{
    Q_OBJECT
  private slots:
    void toUpper();

  private:
    MainWindow* mainwindow;
};

void TestQString::toUpper()
{
    boost::filesystem::recursive_directory_iterator it;
    mainwindow = new MainWindow(nullptr);
    QString str = "Hello";
    QCOMPARE(str.toUpper(), QString("HELLO"));
    delete mainwindow;
}

QTEST_MAIN(TestQString)

#include "testTest.moc"