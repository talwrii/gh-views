import setuptools

setuptools.setup(
    name='gh-views',
    version="3.2.0",
    author='@readwithai',
    long_description_content_type='text/markdown',
    author_email='talwrii@gmail.com',
    description='Fetch number of views or clones of a github repo and mantain a timeline.',
    license='BSD',
    keywords='github, statistics, views',
    url='https://github.com/talwrii/gh-views',
    packages=["gh_views"],
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': ['gh-views=gh_views.main:main']
    }
)
