from setuptools import setup

setup(
    name="shadowsocks-manager-py",
    version="3",
    license='MIT License',
    description="Multiple User Manage and access record",
    author='magicalbomb',
    author_email='presentationmeme@qq.com',
    url='https://github.com/MagicalBomb/shadowsocks-manager-py',
    packages=['ss_mgr'],
    package_data={
        'shadowsocks': ['README.md', 'LICENSE']
    },
    install_requires=[],
    entry_points="""
    [console_scripts]
    ss-mgr = ss_mgr.manager:main
    """,
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
)

