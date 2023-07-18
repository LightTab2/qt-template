#include "mainwindow.h"
#include <QApplication>
#include <boost/filesystem.hpp>

int main(int argc, char *argv[])
{
    boost::filesystem::recursive_directory_iterator it;
    QApplication a(argc, argv);
    MainWindow w;
    w.show();
    return a.exec();
}

void befriendedFunction(MainWindow win)
{
    win.func2(12);
}