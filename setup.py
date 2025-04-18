import setuptools

setuptools.setup(
    name='gh-views',
    version="3.0.2",
    author='@readwithai',
    long_description_content_type='text/markdown',
    author_email='talwrii@gmail.com',
    description='',
    license='BSD',
    keywords='github, statistics',
    url='https://github.com/talwrii/gh-views',
    packages=["gh_views"],
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': ['gh-views=gh_views.main:main']
    }
)
