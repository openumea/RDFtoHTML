from setuptools import setup, find_packages

setup(
    name='rdf-to-html',
    version=1.0,
    description='RDF to HTML converter',

    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2.7",
    ],
    keywords=['Open Data', 'Linked Open Data', 'RDF', 'DCAT'],
    author='Kim Nilsson',
    author_email='kim.nilsson@dohi.se',
    packages=find_packages(),
    install_requires=[
        'rdflib>=4.2.1',
        'django>=1.8.6',
        'requests>=2.8.1',
    ],
    entry_points={
        'console_scripts': [
            'rdf-to-html=rdfconv.main:main',
        ],
    },
)