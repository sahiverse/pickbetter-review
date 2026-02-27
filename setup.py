from setuptools import setup, find_packages

setup(
    name="app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=1.4.0",
        "alembic>=1.7.0",
        "psycopg2-binary>=2.9.0",
        "python-dotenv>=0.19.0",
    ],
)
