from setuptools import setup

setup(
    name="rrequests",
    version="0.1.0",
    description="Empower requests with resilience",
    author="Leo Antunes",
    author_email="antunesleo4@gmail.com",
    packages=["rrequests"],
    install_requires=[
        "requests==2.30",
        "pybreaker==1.0.1",
    ],
)
