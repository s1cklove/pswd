import os.path

from setuptools import setup, find_packages

def readme():
  with open('README.md', 'r') as f:
    return f.read()

setup(
    name='pswd',
    version='1.0.0',
    author='romanzinin',
    author_email='roman.s.zinin@gmail.com',
    description='CLI Password manager with RSA encryption',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/s1cklove',
    packages=find_packages(),
    install_requires=[
        'cryptography',
        'click',
        'pyperclip'
    ],
    project_urls={
        'GitHub': 'https://github.com/s1cklove/pswd',
    },
    entry_points={
        'console_scripts': [
            'pswd = pswd.pswd:cli'
        ],
    }
)
