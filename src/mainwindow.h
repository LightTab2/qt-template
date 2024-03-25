#pragma once
#include <QMainWindow>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

struct someStruct
{
    int x, y, z;
};

namespace myOwnNamespace
{
    constexpr int constant = 10;

    void someFunc();
}

namespace myOwnNamespace2
{
    constexpr int constant2 = 11;
}

/// \brief Some class
/// 
/// Renders a window, I guess.
class MainWindow : public QMainWindow
{
    friend class QObject;
    /// Not really important.
    friend void befriendedFunction(MainWindow win);
    Q_OBJECT

public:
    class Point
    {
        int x, y;
    };
    /// Just an int.
    typedef int someType;
    MainWindow(QWidget* parent = nullptr);
    /// \param param some param
    /// \returns Always `false`.
    bool func1(int param) const
    {
        return false;
    }

    static const bool static_func1(int param)
    {
        return true;
    }

    ~MainWindow();

    /// Int without meaning.
    static int static_var1;
    /// Int without meaning but not static.
    int var1;

public slots:
    void slot(int param)
    {

    }

signals:
    void signal(int param);

protected:
    bool func2(int param) const
    {
        return true;
    }
    static bool static_func2(int param) noexcept
    {
        return true;
    }
    static int static_var2;
    int var2;
private slots:
    void privateSlot(int param)
    {

    }
private:
    bool func3(int param)
    {
        return true;
    }
    static bool static_func3(int param) noexcept
    {
        return true;
    }
    static int static_var3;
    int var3;
    Ui::MainWindow* ui;
};

class DifferentWindow : public MainWindow
{
    int somethingNew;
};
