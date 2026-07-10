#include <QTest>

#include <QString>

#include <boost/version.hpp>
#include <gsl/gsl>

class IntegrationSmokeTest : public QObject
{
    Q_OBJECT

  private slots:
    void qtBoostGslLinkTogether()
    {
        QString s = QStringLiteral("template");
        QVERIFY(!s.isEmpty());
        QVERIFY(BOOST_VERSION >= 109100); // Boost header links AND pins boost >= 1.91.0
        int v = 7;
        gsl::not_null<int*> p(&v); // ms-gsl links
        QCOMPARE(*p, 7);
    }
};

QTEST_MAIN(IntegrationSmokeTest)
#include "integrationSmokeTest.moc"
