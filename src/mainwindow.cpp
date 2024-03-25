#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <boost/multiprecision/integer.hpp>

#include "Exceptions/Exceptions.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), 
      ui{ new Ui::MainWindow }
{
    boost::multiprecision::int1024_t bigInt;
    ui->setupUi(this);
    this->setWindowIcon(QIcon(":/resource/icon/icon_32x32.png"));
    this->setWindowTitle("Qt Template");
}

MainWindow::~MainWindow()
{
    delete ui;
}
