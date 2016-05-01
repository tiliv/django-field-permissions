from setuptools import setup, find_packages

setup(name='django-field-permissions',
      version='0.1',
      description='A starting place for field-level permissions',
      author='Tim Valenta',
      author_email='tonightslastsong@gmail.com',
      url='https://github.com/tiliv/django-field-permissions',
      license='MIT',
      classifiers=[
           'Environment :: Web Environment',
           'Framework :: Django',
           'Intended Audience :: Developers',
           'Operating System :: OS Independent',
           'Programming Language :: Python',
           'Topic :: Software Development',
      ],
      packages=find_packages(),
      install_requires=['django>=1.8'],
)
