#include <QtTest>

#include <gsl/gsl>

class GslLinkTest : public QObject
{
    Q_OBJECT

  private slots:
    void notNullHoldsPointer()
    {
        int value = 42;
        gsl::not_null<int*> ptr(&value);
        QCOMPARE(*ptr, 42);
    }
};

QTEST_MAIN(GslLinkTest)
#include "gslLinkTest.moc"
