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
    util.download(
        "https://mx-cdn-test2.s3.eu-west-1.amazonaws.com/mx-buildpack/experimental/metering/metering-sidecar-test.tar.gz?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEG0aCWV1LXdlc3QtMSJHMEUCIQDycAl%2FVc4gNZNyAe2sCqu%2F6mdixhTSvuMYA4pXANRvXQIgcleJzkVc%2F9L7aD2eVztPdUKH84KGyqxgg7XvyW34%2Bd4q5QUINhAAGgwxNDc4Njg3ODUzMTYiDAObQqZG8NMftQHrfCrCBVoh%2FpFY%2FQPqIwQMMfNjPq7S%2BPU9CB6js%2FtX6Qma31vo1h8c39tqYU1veHCRdUGbF0%2FSKTeJPEqWrbOeO8BP7%2BX3Y2Sd3ZG2Ce3%2FCt7AVeOOavyaEuITbDlibfrnPRHw2hSU6D7xCj9ggjFvdbGG1TAex35hDQIVp6N%2FKgRdSOHmsDVlw50OBqqbn6d1eB9Fb2cCoSBU3tnIh2AG%2B61EsS6phAz5J818n6Pwld5yXzLAbKVOIc0Ren7XkDwmtMAq6edJoOYX6WuTTgmkX%2Bbp1wxFbYNuvMT0jp28A6MPABNu3389QgY6dYSPKPQOIiu6JWijXyvJ9pbZJjZR7tjlY0OAF8Na3Id3lwYqhaglh%2F4bJzb%2FogOzMz6zYoRg2SS6Xyyz3DqZyOpCNiiNDn6895kNfsrwy6fafg0aRuWVp4mdk3WbtzFB2yTWy4Oe6WI5wUtyA0GswF7fE7W4BBWga9WIiY7sq5Z0REok3VIXxXXLkGwYm50PILa4o16ZunsBS0%2B0FslM0h0bJ3x2E8%2BFE3YglL%2BBw2DZ%2F5h3J8pRftxe2dtsdLZLEP6Ei3p9fBC12WlL%2BFbitc9doJjKNe9XPYSmbE2HVBZ6%2Fm76noIN8%2FNP9EgNGLPm6oYLjKyY5sxQJ9WTh9HziFVFDcgM%2BxSEjOoBHwptxt7H1DhQ5TSgotJlUKniSFASTJtNIUbaIWFvVD9nyE1InDi%2F%2BBmi5OeAq4eqCtvm4remnuSaWKwX6APTV3n1o9plpz%2FRP%2BtyphuKbyvK53vSLwcOgNix1Vd2IaW1IpN%2FZnlrj%2Bn2DonMuH68ie9GJaiXra3szRZl%2FVOWYLliIEMTMgAUU1R7zt0CWZbvC2wjgk1BBHi0jnQD1EFg8pWkLQFaKor7q1ctH%2Fjezr3H6ZXr5g%2BHVnt2HUTOaYEbxQIFaYK8faHrweA7NKa8EyYwlaTRyAY6wwK9JSp0Sw92OHZwqzl3sciL1LW0gdQK%2B4YLZSxaCc4mzkvZGrBY0kEr0dl4T1g7GHhS5AQHgwbzt6JSK%2Fr%2BfqTphkcc5ZZ0bLS%2FEmNXzPLjXYLoL5pSA6yZAey93k82Y7YuI6oUqoyZSUnTNi0cq%2BIpqk65sn%2BY8FRSKiL3j198PjNxV%2F3fMP%2BKJBZPRfs%2FBMPYgtDPN2TZB4o%2FXXiE%2BwqHpy0wdbcPzVsMqKWdGIMQp5T8zRpXgbk7nagH019TBNu62v6UlW5q%2BQHg%2B2C4jIzDsU5xC38vFkcQKbN4U7Pqo48NPuIp1HXB98mPmz7Z63GLDYRTWvpzr2eqhpiyavsq6AkBkix9wkTTITOkgcAuLF2WTmTZE5uyaU1ud8iqTdpYBI1wnseJt6pVm5FFaoBSvs%2F866R9IQbXCJT66luNJiG%2BMg%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIASE3NKTKSO6TJHWB3%2F20251112%2Feu-west-1%2Fs3%2Faws4_request&X-Amz-Date=20251112T130630Z&X-Amz-Expires=600&X-Amz-SignedHeaders=host&X-Amz-Signature=873076bb2585603bbdebbfa7adfb6e921c1724bde61ad93786d686de1b2e5c00",
        os.path.join(build_path, NAMESPACE),
        cache_dir=cache_dir,
    )


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

            # project_id = _get_project_id(
            #     os.path.join(build_path, "model", "metadata.json")
            # )
            config = {"ProjectID": "ac378eea-6f7e-4161-b6c7-42c95650e614"}

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
