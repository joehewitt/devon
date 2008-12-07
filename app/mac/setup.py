
from distutils.core import setup
import py2app, sys

plist = dict(
    NSPrincipalClass='DevonApp',
    CFBundleIdentifier='com.joehewitt.Devon',
    NSAppleScriptEnabled="YES",
    OSAScriptingDefinition="Devon.sdef",
    CFBundleDocumentTypes=[
        dict(
            CFBundleTypeExtensions=["dev"],
            CFBundleTypeIconFile="Devon.icns",
            CFBundleTypeName="Devon Project",
            CFBundleTypeRole="Viewer",
            LSItemContentTypes=["com.joehewitt.Devon.project"],
            NSDocumentClass="DevonProject",
        ),
        dict(
            CFBundleTypeExtensions=["test"],
            CFBundleTypeIconFile="Devon.icns",
            CFBundleTypeName="Devon Unit Test",
            CFBundleTypeRole="Viewer",
            LSItemContentTypes=["com.joehewitt.Devon.test"],
            NSDocumentClass="DevonUnitTest",
        ),
    ],
    UTExportedTypeDeclarations=[
        dict(
            UTTypeDescription="Devon Project",
            UTTypeConformsTo=["public.text", "public.plain-text"],
            UTTypeIconFile="Devon.icns",
            UTTypeIdentifier="com.joehewitt.Devon.project",
            UTTypeTagSpecification={
                "com.apple.ostype": "TEXT",
                "public.filename-extension": ["dev"],
            },
        ),
        dict(
            UTTypeDescription="Devon Unit Test",
            UTTypeConformsTo=["public.text", "public.plain-text"],
            UTTypeIconFile="Devon.icns",
            UTTypeIdentifier="com.joehewitt.Devon.test",
            UTTypeTagSpecification={
                "com.apple.ostype": "TEXT",
                "public.filename-extension": ["test"],
            },
        ),
        dict(
            UTTypeDescription="Devon Bugs",
            UTTypeConformsTo=["public.text", "public.plain-text"],
            UTTypeIconFile="Devon.icns",
            UTTypeIdentifier="com.joehewitt.Devon.bugs",
            UTTypeTagSpecification={
                "com.apple.ostype": "TEXT",
                "public.filename-extension": ["bugs"],
            },
        ),
    ]
)

setup(
    name="Devon",
    app=["Devon.py"],
    data_files=["Devon.sdef"],
    options=dict(
        py2app=dict(
            iconfile="Devon.icns",
            packages=["devon"],
            plist=plist,
        )
     ),
)
