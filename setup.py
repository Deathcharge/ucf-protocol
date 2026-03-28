from setuptools import setup, find_packages

setup(
    name='ucf-protocol',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # Add any dependencies here, e.g., 'requests>=2.20.0',
    ],
    author='Manus AI',
    description='Universal Coordination Framework Protocol for multi-agent systems',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Deathcharge/ucf-protocol',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
)
