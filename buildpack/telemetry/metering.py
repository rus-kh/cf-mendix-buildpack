import logging
import os
import json
import subprocess

from buildpack import util
from buildpack.infrastructure import database

NAMESPACE = "metering"
BINARY = "metering-sidecar"
DEPENDENCY = f"{NAMESPACE}.sidecar"
SIDECAR_DIR = os.path.join("/home/vcap/app", NAMESPACE)
SIDECAR_CONFIG_FILE = "conf.json"


def _download(build_path, cache_dir):
    util.resolve_metering_dependency(
        DEPENDENCY,
        os.path.join(build_path, NAMESPACE),
        buildpack_dir=buildpack_dir,
        cache_dir=cache_dir,
        ignore_cache=True
    )
    # util.download(
    #     "https://mx-cdn-test2.s3.eu-west-1.amazonaws.com/mx-buildpack/experimental/metering/metering-sidecar-test.tar.gz?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEG4aCWV1LXdlc3QtMSJIMEYCIQClQ2hRkh7UJgugfhdt%2Fe0NPOOliBMlcoR%2FG9VB7NTLJQIhAO%2F5ohVxw40EQNcrR303Pmy%2Fz7dnGufsgK2lgsr0H91gKuUFCDcQABoMMTQ3ODY4Nzg1MzE2Igzcm5TwFfhxSVjOkPgqwgVtM21Vo%2BLzM0crsYSpptBYGwpfn%2FvBxyT84WBfTOuypKOCryYpMO4B22HEzCcgiVUUy2%2F4A2Lm15VUUBXcVOi32Kzk6b4Rg6h%2BN63TmiVDfT9XDXl9QKiLBIVM713aQ4BcS7vRuBxmFqCDZ9RDbNeQ6x8b3GkpyPIyLv75F40iBHLNRYmzSEMQyN4e9LR2nf%2BZlPP61CA8bg2VnGgcz1srCGWeVwfKs1j9fsHnv57H1aAYEa9FM%2F5RPNlGYVL%2Fs75S84swrGBNiAHZC0E61sEvYR2g67E5zdVc3X8XD21aF8AfloC0Glm%2BNheUgmlIhCBBjb3faZK5qJi3n5hKkTWKiQwPU5%2BuGft8CkvkcmFf1NZTQLaTLP0Gi3%2FelHFEGCttH8Gg0E4en%2Fk4Yym39K%2F5YR3SnicorxuT6vXiaAsKUT23keAcBdBUoGlfMBCwLEw%2F3ym3PWwWXibcoXWHV6YoV2TSBgRYJen6LXW4c04zFTyxX7k6DVimzTv%2Bsz8QV%2BcZNuc4iexZfxAez4m44c9jpd63%2BldVochIQajPx%2BJrf8FHSTXQwb%2B1FnVpZ7V%2B%2Fn%2FHOk4Pd8JXmTxZK0blSUHArMRYpO8tgp9yITSdnaOhEPQzRJXNqeT4pPnlUipVj4K93wGQDMwOSts0ly%2FTf2NaU%2FYlPnmojS%2B7C5005aKaKAWBC2i3oc80UB5xtUl1TC5L%2BraGnsvtzbu9zj6qTWvDfAfRgWFuOBervwyUPZYQZ1i4SK8UHjimolEwWd4xkG8X5MmFN5nimVSJKg98R%2BpSOHPWk1a6FknRMlJZZZIwwoOOCkyr2otRS5XCfQDz0z%2F1tFZiw%2FxCtwJWrS3ocm52inPMxnENiZjzG6sVm186Jsnq8L4hyGeJtDNlylIDWMlBWU2%2B1m7agcJVFmY6rcCPQul7Jjlk2oP9fGrfvTlJDrK4MJWk0cgGOsICMOM%2FaLQL0VDsfKmXUs5mfYWiPH1jWo4Eqxn1uS35Pm%2BQ72c4RHHiAzmXcJJc5MLqeLaqYlBVeTV6fTzHLSguh7ojWG1N%2BVtogMiDKqF2kT7SRk8PYtymqPS7DTPYrdeWl6Nw9cXaKaBBd8sdE1INIuCliGknwY%2Byr%2Bhudud3sh8DxVe%2BDIKpYCok%2FMfd86%2BUgDFMd6iyOdBTgsYp54JNlReoHZdYrcuA%2FcZ2BYL9MhgOm%2FSpIgniQ%2Fj3m4g5mdgicgaJPSr0C0kRzUe%2FTOVNm1dIWh5JvnSBfz33qHzt9lLrZNFD46tQpxvYqBwfbyi7kq4uuOldAlcN%2Fm6qt44dUP6xKHzAi%2BQV0jd1FFrwKXnCGyeZdWR7MIBQWCFNAnFpWoTGiNX7YvKSLlWoyCecoZPQmVxdyZEkCfOMSRaUYNIRNg%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIASE3NKTKSDSEGA62F%2F20251112%2Feu-west-1%2Fs3%2Faws4_request&X-Amz-Date=20251112T132247Z&X-Amz-Expires=10800&X-Amz-SignedHeaders=host&X-Amz-Signature=cf5ae26ef3be48cce7f09fcb4bb4a80859f87abf8243fa078c0a18590e1905a9",
    #     os.path.join(build_path, NAMESPACE)
    # )

def _is_usage_metering_enabled():
    if "MXUMS_LICENSESERVER_URL" in os.environ:
        return True


def _get_project_id(file_path):
    try:
        with open(file_path) as file_handle:
            data = json.loads(file_handle.read())
            return data["ProjectID"]
    except IOError as ioerror:
        raise Exception(
            f"Error while trying to get the ProjectID. Reason: '{ioerror}'"
        ) from ioerror


def write_file(output_file_path, content):
    if output_file_path is None:
        print(content)
    else:
        try:
            with open(output_file_path, "w") as f:
                json.dump(content, f)
        except Exception as exception:
            raise Exception(
                f"Error while trying to write the configuration to a file. Reason: '{exception}'"  # noqa: C0301
            ) from exception


def _set_up_environment():
    if "MXRUNTIME_License.SubscriptionSecret" in os.environ:
        os.environ["MXUMS_SUBSCRIPTION_SECRET"] = os.environ[
            "MXRUNTIME_License.SubscriptionSecret"
        ]
    if "MXRUNTIME_License.LicenseServerURL" in os.environ:
        os.environ["MXUMS_LICENSESERVER_URL"] = os.environ[
            "MXRUNTIME_License.LicenseServerURL"
        ]
    if "MXRUNTIME_License.EnvironmentName" in os.environ:
        os.environ["MXUMS_ENVIRONMENT_NAME"] = os.environ[
            "MXRUNTIME_License.EnvironmentName"
        ]
    dbconfig = database.get_config()
    if dbconfig:
        os.environ["MXUMS_DB_CONNECTION_URL"] = (
            f"postgres://{dbconfig['DatabaseUserName']}:"
            f"{dbconfig['DatabasePassword']}@"
            f"{dbconfig['DatabaseHost']}/"
            f"{dbconfig['DatabaseName']}"
        )
    project_id = _get_project_id(os.path.join(SIDECAR_DIR, SIDECAR_CONFIG_FILE))
    os.environ["MXUMS_PROJECT_ID"] = project_id
    e = dict(os.environ.copy())
    return e


def _is_sidecar_installed():
    if os.path.exists(os.path.join(SIDECAR_DIR, BINARY)):
        if os.path.exists(os.path.join(SIDECAR_DIR, SIDECAR_CONFIG_FILE)):
            return True
        else:
            logging.info("Metering sidecar configuration not found")
    else:
        logging.info("Metering sidecar not found")
    return False


def stage(buildpack_path, build_path, cache_dir):
    try:
        if _is_usage_metering_enabled():
            logging.info("Usage metering is enabled")
            _download(buildpack_path, build_path)

            project_id = _get_project_id(
                os.path.join(build_path, "model", "metadata.json")
            )
            config = {"ProjectID": project_id}

            logging.info("Writing metering sidecar configuration file...")
            write_file(
                os.path.join(build_path, NAMESPACE, SIDECAR_CONFIG_FILE),
                config,
            )
        else:
            logging.info("Usage metering is NOT enabled")
    except Exception as e:
        logging.info(
            f"Encountered an exception while staging the metering sidecar: {e}"
        )


def run():
    try:
        if _is_usage_metering_enabled() and _is_sidecar_installed():
            logging.info("Starting metering sidecar")
            subprocess.Popen(
                os.path.join(SIDECAR_DIR, BINARY),
                env=_set_up_environment(),
            )
    except Exception:
        logging.info(
            "Encountered an exception while starting the metering sidecar."
            "This is nothing to worry about."
        )
