from setuptools import setup

setup(
    name="shadowsocks-manager-py",
    version="Origin",
    license='MIT License',
    description="Multiple User Manage and access record",
    author='magicalbomb',
    author_email='presentationmeme@qq.com',
    url='https://github.com/MagicalBomb/shadowsocks-manager-py',
    packages=['shadowsocks-mgr'],
    package_data={
        'shadowsocks': ['README.md', 'LICENSE']
    },
    install_requires=[],
    entry_points="""
    [console_scripts]
    ssserver-mgr = shadowsocks-mgr.manager:main
    """,
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
    ],
)