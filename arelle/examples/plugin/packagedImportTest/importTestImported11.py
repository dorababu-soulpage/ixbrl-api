'''
pluginPackages test case

See COPYRIGHT.md for copyright information.
'''
from arelle.Version import authorLabel, copyrightLabel

def foo():
    print ("imported packaged plug-in relative imported 1.1")

__pluginInfo__ = {
    'name': 'Package Relative Import 1.1',
    'version': '0.9',
    'description': "This is a packaged relative imported plugin.",
    'license': 'Apache-2',
    'author': authorLabel,
    'copyright': copyrightLabel,
    # classes of mount points (required)
    'Import.Packaged.Entry7': foo,
    # imported plugins
}
