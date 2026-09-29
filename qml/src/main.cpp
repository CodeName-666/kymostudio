/****************************************************************************
**
** Copyright (C) 2021 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of Qt Quick Studio Components.
**
** $QT_BEGIN_LICENSE:GPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 3 or (at your option) any later version
** approved by the KDE Free Qt Foundation. The licenses are as published by
** the Free Software Foundation and appearing in the file LICENSE.GPL3
** included in the packaging of this file. Please review the following
** information to ensure the GNU General Public License requirements will
** be met: https://www.gnu.org/licenses/gpl-3.0.html.
**
** $QT_END_LICENSE$
**
****************************************************************************/

#include <QGuiApplication>
#include <QCoreApplication>
#include <QQmlApplicationEngine>
#include <QApplication>
#include <QDir>
#include <QFileInfo>
#include <QFile>
#include <QDebug>
#include <QSettings>
#include <QQuickStyle>

#include "app_environment.h"
#include "import_qml_plugins.h"

namespace {

void ensureQuickControlsConfig()
{
    const QString appDir = QCoreApplication::applicationDirPath();
    const QStringList candidates = {
        QDir(appDir).filePath("qtquickcontrols2.conf"),
        QDir(appDir).filePath("../qtquickcontrols2.conf"),
        QDir(appDir).filePath("../Resources/qtquickcontrols2.conf"),
        QDir(appDir).filePath("../qml/qtquickcontrols2.conf"),
        QDir(appDir).filePath("../../qml/qtquickcontrols2.conf")
    };

    for (const QString &path : candidates) {
        if (QFileInfo::exists(path)) {
            qputenv("QT_QUICK_CONTROLS_CONF", QFile::encodeName(path));
            return;
        }
    }

    qWarning() << "qtquickcontrols2.conf not found in expected locations. "
                  "Qt Quick Controls will fall back to default styling.";
}

QString resolveControlsStyle()
{
    QSettings settings;
    const QString stored = settings.value(QStringLiteral("ui/controlsStyle"),
                                          QStringLiteral("Fusion")).toString();
    if (stored.isEmpty())
        return QStringLiteral("Fusion");
    return stored;
}

}

int main(int argc, char *argv[])
{
    QCoreApplication::setOrganizationName(QStringLiteral("PlotterApp"));
    QCoreApplication::setOrganizationDomain(QStringLiteral("plotter.app"));
    QCoreApplication::setApplicationName(QStringLiteral("PlotterApp"));

    set_qt_environment();

    const QString controlsStyle = resolveControlsStyle();
    qputenv("QT_QUICK_CONTROLS_STYLE", controlsStyle.toUtf8());
    QQuickStyle::setStyle(controlsStyle);

    QGuiApplication app(argc, argv);
    ensureQuickControlsConfig();

    QQmlApplicationEngine engine;
    const QUrl url(u"qrc:Main/main.qml"_qs);
    QObject::connect(
                &engine, &QQmlApplicationEngine::objectCreated, &app,
                [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl)
            QCoreApplication::exit(-1);
    },
    Qt::QueuedConnection);

    engine.addImportPath(QCoreApplication::applicationDirPath() + "/qml");
    engine.addImportPath(":/");

    engine.load(url);

    if (engine.rootObjects().isEmpty()) {
        return -1;
    }

    return app.exec();
}
