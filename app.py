import json, io
import zipfile
import os, shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import uuid
import boto3
import requests
import pandas as pd
from decouple import config
from datetime import datetime
from bs4 import BeautifulSoup

from xml_generation.html_parser import HtmlTagParser
from xml_generation.generate_xsd import XSDGenerator
from xml_generation.generate_pre import PreXMLGenerator
from xml_generation.generate_def import DefXMLGenerator
from xml_generation.generate_cal import CalXMLGenerator
from xml_generation.generate_lab import LabXMLGenerator
from xml_generation.generate_xhtml import XHTMLGenerator

# from auto_tagging.tagging import auto_tagging
from flask import Flask, request, render_template, url_for
from utils import (
    extract_html_elements,
    get_db_record,
    get_split_file_record,
    get_client_record,
    get_client_record,
    s3_uploader,
    read_images_from_folder,
    read_html_from_folder,
    upload_image_to_s3,
)
from rule_based_tagging import RuleBasedTagging

app = Flask(__name__, static_folder="static/", static_url_path="/")

storage_dir = "data"
base_dir = Path().absolute()
# create data directory if not exits
Path(f"{base_dir}/{storage_dir}").mkdir(parents=True, exist_ok=True)
storage_dir = Path(storage_dir).absolute()


def download_files(url):
    # download zip file
    os.chdir(storage_dir)
    download_url = f"wget {url}"
    subprocess.call(download_url, shell=True)

    # unzip files
    zipfile = url.split("/")[-1]
    file = zipfile.removesuffix(".zip")
    subprocess.call(f"unzip -o {storage_dir}/{zipfile}", shell=True)

    # unzip is done remove .zip file
    file_to_remove = Path(f"{storage_dir}/{zipfile}/")
    file_to_remove.unlink()
    os.chdir(base_dir)

    return file


def download_html_file(url):
    dirname = os.path.basename(url).replace("-", "").replace(".", "")
    path = Path(f"{storage_dir}/validation/{dirname}").mkdir(
        parents=True, exist_ok=True
    )
    # download zip file
    os.chdir(f"{storage_dir}/validation/{dirname}")
    download_url = f"wget {url}"
    subprocess.call(download_url, shell=True)
    os.chdir(base_dir)

    return dirname


def get_validation_logs(file):
    logs_html = f"{storage_dir}/{file}/out/RenderingLogs.htm"
    try:
        with open(logs_html, "r", encoding="utf-8") as file:
            html_content = file.read()
            logs_df = pd.read_html(html_content)[0]
            return logs_df.to_dict()
    except:
        return {"message": "logs not found"}


def get_html_validation_logs(file):
    logs_html = f"{file}/out/RenderingLogs.htm"

    if Path(logs_html).is_file():
        with open(logs_html, "r", encoding="utf-8") as file:
            html_content = file.read()
            logs_df = pd.read_html(html_content)[0]
            return logs_df.to_dict()
    else:
        return {"message": "validated successfully"}


@app.route("/")
def index():
    return {"message": "welcome to ixbrl viewer"}


@app.route("/api/html-validation")
def html_validation():
    query_params = request.args
    url = query_params.get("q", None)
    if url is None:
        return {"message": "query params required."}

    file = download_html_file(url)

    # validation process
    file = f"{base_dir}/data/validation/{file}"
    plugin = f"{base_dir}/EdgarRenderer"

    print("\n===============[html validation started]===============\n")

    validation_cmd = f"python arelleCmdLine.py --plugins={plugin} -f {file} --disclosureSystem efm-pragmatic --validate -r {file}/out"
    print(validation_cmd, "===================[validation command]================")

    subprocess.call(validation_cmd, shell=True)
    # get logs
    response = get_html_validation_logs(file)
    return response


def validation(file_path):
    # validation process
    file = file_path
    plugin = f"{base_dir}/EdgarRenderer"
    logs_path = f"{file}/logs"

    print("\n===============[validation started]===============\n")

    validation_cmd = f"python arelleCmdLine.py -f {file} --plugins {plugin} --disclosureSystem efm-pragmatic --validate -r {file}/out --logFile={logs_path}/validation.logs"
    subprocess.call(validation_cmd, shell=True)
    # get logs
    response = get_validation_logs(file)
    return response


def upload_zip_to_s3(name, zip_file):
    """this function is used to upload the files to the s3 server and return the url"""
    # name is s3 file name
    access_key = config("AWS_S3_ACCESS_KEY_ID")
    secret_key = config("AWS_S3_SECRET_ACCESS_KEY")
    region = config("AWS_S3_REGION")
    bucket = config("AWS_S3_BUCKET_NAME")

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    s3 = session.resource("s3")
    try:
        # Read the contents of the local zip file
        with open(zip_file, "rb") as file:
            zip_contents = file.read()

        # Use put_object to upload the zip file
        s3.Bucket(bucket).put_object(
            Key=name,
            Body=zip_contents,
            ACL="public-read",
            ContentType="application/zip",  # Adjust content type as needed
        )

        # Determine the region for building the S3 URL
        location = (
            session.client("s3")
            .get_bucket_location(Bucket=bucket)
            .get("LocationConstraint", "")
        )
        if location:
            s3_url = f"https://s3-{location}.amazonaws.com/{bucket}/{name}"
        else:
            # Handle the case where the location is None (e.g., us-east-1)
            s3_url = f"https://s3.amazonaws.com/{bucket}/{name}"

        return s3_url

    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None


def zip_html_xml_files(directory, zip_name):
    # Create a zip file
    with zipfile.ZipFile(zip_name, "w") as zipf:
        # Iterate through all files in the directory
        for foldername, subfolders, filenames in os.walk(directory):
            for filename in filenames:
                # Check if the file is an HTML or XML file
                if filename.endswith((".htm", ".xsd", ".xml")):
                    # Create the complete file path
                    file_path = os.path.join(foldername, filename)
                    # Add the file to the zip archive
                    zipf.write(file_path, os.path.relpath(file_path, directory))


def get_plugins(desired_names):
    plugins_path = os.path.join(app.static_folder, "plugins")
    if os.path.exists(plugins_path) and os.path.isdir(plugins_path):
        # List all items in the plugins directory
        subdirectories = [
            os.path.join(plugins_path, name)
            for name in os.listdir(plugins_path)
            if os.path.isdir(os.path.join(plugins_path, name)) and name in desired_names
        ]
        # Join the subdirectory names with a pipe separator
        return "|".join(subdirectories)
    else:
        return ""


def run_arelle(input_file, output_dir):
    pluginsPath = get_plugins(["EdgarRenderer"])

    # Command to run Arelle with input HTML and save the output in the specified directory
    command = [
        "arelleCmdLine",
        "-f",
        input_file,
        "-v",
        "--efm",
        "--plugins",
        pluginsPath,
        "--reportFormat",
        "HtmlAndXml",
        "-r",
        output_dir,
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
        print(f"View generated successfully and saved in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error running Arelle: {e}")


def ixbrl_viewer_file_generation(file):

    # Create a unique folder for the output
    unique_folder = str(uuid.uuid4())
    output_folder = os.path.join(app.static_folder, unique_folder)
    xbrl_url = None

    file_path = file

    try:
        output_path = f"{app.static_folder}/viewer"
        output_filename = f"/viewer/{unique_folder}/FilingSummary.htm"

        run_arelle(file_path, os.path.join(output_path, unique_folder))
        url = url_for("static", filename=output_filename)

        xbrl_url = url

    except Exception as e:
        # Check if output_folder exists
        if Path(output_folder).exists():
            os.rmdir(output_folder)
            os.remove(file_path)

    # Zip the folder
    # shutil.make_archive(file, "zip", file)
    zip_html_xml_files(file, f"{file}.zip")

    # Upload the zip file to S3
    zip_file_path = f"{file}.zip"

    # Parse the URL
    parsed_url = urlparse(zip_file_path)

    # Extract the path component and create a Path object
    path = Path(parsed_url.path)

    # Get the filename
    filename = path.name
    ixbrl_package_url = upload_zip_to_s3(filename, zip_file_path)

    # Remove the file, zip directory
    shutil.rmtree(file)
    os.remove(zip_file_path)

    return ixbrl_package_url, xbrl_url


@app.route("/api/rule-based-tagging", methods=["POST"])
def rule_based_tagging_view():
    file_id = request.json.get("file_id", None)
    xlsx_file = config("RULE_BASED_XLSX")
    record = get_db_record(file_id=file_id)
    html_file = record.get("url", None)
    cik = request.json.get("cik", None)
    form_type = record.get("formType", None)
    if file_id is None or cik is None:
        return {"error": "invalid input file id, cik is required"}
    if html_file is None:
        return {"error": "This file id done not have any html files"}

    # # Read the contents of the file without saving it
    # add_tag_to_keyword(file_id, html_file, xlsx_file)

    # add_tag_to_keyword(file_id, html_file, xlsx_file, cik, form_type)
    rbt = RuleBasedTagging(html_file, xlsx_file, file_id, cik, form_type)
    rbt.start()

    # thread = Thread(target=add_tag_to_keyword, args=(file_id, html_file, xlsx_file))
    # thread.start()

    return {"message": "rule based tagging is started "}, 200


@app.route("/api/xml-generation", methods=["GET", "POST"])
def generate_xml_schema_files():
    split_file = False
    if "file_id" in request.json.keys():
        file_id = request.json.get("file_id")
        record = get_db_record(file_id=file_id)

        extra = record.get("extra", None)
        if extra is not None:
            html_file = extra.get("url")
        else:
            html_file = record.get("url")

    if "split_file_id" in request.json.keys():
        split_file_id = request.json.get("split_file_id")
        split_file_record = get_split_file_record(file_id=split_file_id)

        file_id = split_file_record.get("id")
        record = get_db_record(file_id=split_file_record.get("fileId"))

        extra = split_file_record.get("extra", None)
        if extra is not None:
            html_file = extra.get("url")
        else:
            html_file = split_file_record.get("url")

        split_file = True

    client_id = record.get("clientId")
    client_data = get_client_record(client_id=client_id)

    cik = client_data.get("cik", "")
    ticker = client_data.get("ticker", "")

    period_end = record.get("periodTo", "")

    filename = record.get("fileName")

    elements_data = record.get("elementsData")

    # Convert string to datetime object
    datetime_obj = datetime.strptime(str(period_end), "%Y-%m-%d %H:%M:%S")

    # Convert datetime object to desired format
    output_date = datetime_obj.strftime("%Y%m%d")

    # period end date
    filing_date = output_date

    company_website = client_data.get("website", "")

    html_elements = extract_html_elements(html_file)

    # Create an instance of HtmlTagParser
    parser = HtmlTagParser()

    # Get the formatted data for all tags
    data = parser.process_tags(html_elements)

    # # write data into output.json file
    # with open(f"data/{filename}.json", "w") as output:
    #     output.write(json.dumps(data))

    # # read json data from data.json file
    # with open(f"{filename}.json", "r") as file:
    #     data = json.load(file)

    args = data, ticker, filing_date, company_website, client_id
    # Initialize XMLGenerators and generate the pre.xml file.
    xsd_generator = XSDGenerator(*args)
    xsd_generator.generate_xsd_schema()

    args = data, filing_date, ticker, company_website, client_id, elements_data
    pre_generator = PreXMLGenerator(*args)
    pre_generator.generate_pre_xml()

    args = data, ticker, filing_date, company_website, client_id, elements_data
    def_generator = DefXMLGenerator(*args)
    def_generator.generate_def_xml()

    args = data, filing_date, ticker, company_website, client_id
    cal_generator = CalXMLGenerator(*args)
    cal_generator.generate_cal_xml()

    args = data, filing_date, ticker, company_website, client_id, elements_data
    lab_generator = LabXMLGenerator(*args)
    lab_generator.generate_lab_xml()

    # generate xHTML file
    args = (
        data,
        filing_date,
        ticker,
        cik,
        file_id,
        html_file,
        filename,
        split_file,
        company_website,
    )
    xhtml_generator = XHTMLGenerator(*args)
    xhtml_generator.generate_xhtml_file()

    file_path = f"data/{ticker}-{filing_date}"

    package_url, xbrl_url = ixbrl_viewer_file_generation(file_path)

    return {
        "messages": "XML Files generated successfully.",
        "ixbrl_package_url": package_url,
        "xbrl_url": xbrl_url,
    }


@app.route("/ix")
def viewer():
    return render_template("ix.html")


@app.route("/api/upload-file", methods=["POST"])
def upload():
    from boto3 import Session

    url = request.json.get("url")
    filename = os.path.basename(url).replace(".htm", ".txt")

    response = requests.get(url)

    access_key = config("AWS_S3_ACCESS_KEY_ID")
    secret_key = config("AWS_S3_SECRET_ACCESS_KEY")
    region = config("AWS_S3_REGION")
    bucket = config("AWS_S3_BUCKET_NAME")

    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    s3 = session.resource("s3")

    # Upload the file
    s3.Bucket(bucket).put_object(
        Key=filename,
        Body=response.content,
        ACL="public-read",
        ContentType="application/octet-stream",
    )

    # Generate and return the URL
    response_url = f"https://{bucket}.s3.amazonaws.com/{filename}"

    return {"url": response_url}


@app.route("/api/upload-zip", methods=["POST"])
def zip_upload():

    html_url = None

    url = request.json.get("zip_url")
    # Download the zip file
    response = requests.get(url)
    # Check if the download was successful
    response.raise_for_status()

    # Parse the URL to get the path
    parsed_url = urlparse(url)

    # Extract the filename from the path using pathlib
    path = Path(parsed_url.path)

    # Get the filename without extension
    output_folder = path.stem
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(output_folder)

    uploaded_images: dict = {}
    html_files: dict = {}

    images = read_images_from_folder(output_folder)
    html_paths = read_html_from_folder(output_folder)

    bucket_name = config("AWS_S3_BUCKET_NAME")
    for filename, img_path in images:
        uploaded_url = upload_image_to_s3(img_path, bucket_name, filename)
        uploaded_images[filename] = uploaded_url

    for filename in os.listdir(output_folder):
        if filename.endswith((".htm", ".html")):
            input_html_file = os.path.join(output_folder, filename)

            with open(input_html_file, "r") as html_file:
                soup = BeautifulSoup(html_file, "html.parser")
                a_tags = soup.find_all("a")
                for a_tag in a_tags:
                    href = a_tag.get("href", None)
                    if href:
                        a_href: str = a_tag["href"]
                        html_files[input_html_file] = []
                        if a_href.endswith((".htm", ".html")):
                            html_files[input_html_file].append(a_href)

    uploaded_htmls: dict = {}
    input_html_files = list(html_files.keys())

    if len(input_html_files) == 0:
        for filename in os.listdir(output_folder):
            if filename.endswith((".htm", ".html")):
                input_html_file = os.path.join(output_folder, filename)
                input_html_files.append(input_html_file)

    for filename, html_path in html_paths:
        uploaded_url = upload_image_to_s3(html_path, bucket_name, filename)
        uploaded_htmls[filename] = uploaded_url

    input_html_file = input_html_files[0]
    with open(input_html_file, "r") as html_file:
        soup = BeautifulSoup(html_file, "html.parser")

        img_tags = soup.find_all("img")
        for img in img_tags:
            img_url = img["src"]
            # Assuming img_url is a relative path, construct S3 URL
            s3_url = uploaded_images.get(img_url)
            img["src"] = s3_url

        a_tags = soup.find_all("a")
        for a_tag in a_tags:
            href = a_tag.get("href", None)
            if href:
                # Assuming img_url is a relative path, construct S3 URL
                s3_url = uploaded_htmls.get(href)
                if s3_url:
                    a_tag["href"] = s3_url

        # Save modified HTML back
        with open(input_html_file, "w") as modified_html:
            modified_html.write(str(soup))

        try:
            # Read the file content into memory
            with open(input_html_file, "rb") as f:
                file_content = f.read()

            # Convert the file content to BytesIO
            file_object = io.BytesIO(file_content)
            filename = os.path.basename(input_html_file)
            html_url = s3_uploader(filename, file_object)

        except Exception as e:
            print(str(e))

    # Remove the file, zip directory
    shutil.rmtree(output_folder)
    # os.remove(zip_file_path)

    return {"url": html_url}


if __name__ == "__main__":
    port = config("PORT")
    app.run(host="0.0.0.0", port=port, debug=True)
