import json, io
import zipfile
import os, shutil
import subprocess
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

import boto3
import requests
import pandas as pd
from decouple import config
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString

from xml_generation.database import html_elements_data
from xml_generation.html_parser import HtmlTagParser
from xml_generation.generate_xsd import XSDGenerator
from xml_generation.generate_pre import PreXMLGenerator
from xml_generation.generate_def import DefXMLGenerator
from xml_generation.generate_cal import CalXMLGenerator
from xml_generation.generate_lab import LabXMLGenerator
from xml_generation.generate_xhtml import XHTMLGenerator

# from auto_tagging.tagging import auto_tagging
from flask import Flask, redirect, request, url_for, jsonify
from utils import (
    add_html_elements_to_concept,
    extract_html_elements,
    generate_concepts_dts_sheet,
    # generate_ix_header,
    get_db_record,
    get_split_file_record,
    get_client_record,
    get_filename,
    initialize_concepts_dts,
    update_db_record,
    generate_xml_comments,
    add_datatype_tags,
    remove_ix_namespaces,
    # add_html_attributes,
    get_definitions,
    get_client_record,
    s3_uploader,
    read_images_from_folder,
    upload_image_to_s3,
)
from rule_based_tagging import RuleBasedTagging

app = Flask(__name__)

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


def ixbrl_viewer_file_generation(file):

    ixbrl_file_url = None
    log_file_url = None

    # create viewer folder
    Path(f"{file}/viewer").mkdir(parents=True, exist_ok=True)

    logs_path = f"{file}/logs"

    # Check if logs_path exists
    if Path(logs_path).exists():
        # Remove the existing directory
        shutil.rmtree(logs_path)

    # Create the directory
    Path(logs_path).mkdir(parents=True, exist_ok=True)

    logs_file = f"{logs_path}/iXBRLViewer.logs"

    # ixbrl-file-generation
    plugin = f"{base_dir}/ixbrl-viewer/iXBRLViewerPlugin"

    output_html = f"{file}/viewer/{Path(file).name}-ixbrl-viewer.html"
    viewer_url = "https://cdn.jsdelivr.net/npm/ixbrl-viewer/iXBRLViewerPlugin/viewer/dist/ixbrlviewer.js"

    print("\n===============[ixbrl viewer file generation started]===============\n")

    ixbrl_file_gen_cmd = f"python arelleCmdLine.py --plugins={plugin} -f {file} --save-viewer {output_html} --viewer-url {viewer_url} --logFile={logs_file}"
    # ixbrl_file_gen_cmd = f"python arelleCmdLine.py -f {file} --plugins EdgarRenderer --disclosureSystem efm-pragmatic --validate -r out --report out"
    subprocess.call(ixbrl_file_gen_cmd, shell=True)

    # validation_logs = validation(file)

    # Zip the folder
    shutil.make_archive(file, "zip", file)

    # Upload the zip file to S3
    zip_file_path = f"{file}.zip"

    # Parse the URL
    parsed_url = urlparse(zip_file_path)

    # Extract the path component and create a Path object
    path = Path(parsed_url.path)

    # Get the filename
    filename = path.name
    ixbrl_package_url = upload_zip_to_s3(filename, zip_file_path)

    try:
        # Read the file content into memory
        with open(output_html, "rb") as f:
            file_content = f.read()

        # Convert the file content to BytesIO
        file_object = io.BytesIO(file_content)
        ixbrl_filename = os.path.basename(output_html)

        ixbrl_file_url = s3_uploader(ixbrl_filename, file_object)

    except Exception as e:
        print(str(e))

    try:
        # Read the file content into memory
        with open(logs_file, "rb") as f:
            file_content = f.read()

        # Convert the file content to BytesIO
        file_object = io.BytesIO(file_content)
        ixbrl_filename = os.path.basename(logs_file)

        log_file_url = s3_uploader(ixbrl_filename, file_object)

    except Exception as e:
        print(str(e))

    # Remove the file, zip directory
    # shutil.rmtree(file)
    os.remove(zip_file_path)

    return ixbrl_package_url, ixbrl_file_url, log_file_url


@app.route("/api/xml-files")
def generate_xml_files():
    html = request.args.get("html", None)
    xlsx = request.args.get("xlsx", None)
    file_id = request.args.get("file_id", None)
    html_elements = extract_html_elements(html)

    filename = get_filename(html)
    out_dir = f"{storage_dir}/{Path(html).stem}"
    filepath = f"{storage_dir}/{Path(html).stem}/DTS/{xlsx}"
    logs_path = f"{storage_dir}/{Path(html).stem}/logs"

    # create logs folder
    Path(logs_path).mkdir(parents=True, exist_ok=True)

    print("\n===============[loadFromExcel started]===============\n")

    xml_gen_cmd = f"python arelleCmdLine.py -f {filepath} --plugins loadFromExcel --save-Excel-DTS-directory={out_dir} --logFile={logs_path}/loadFromExcel.logs"
    subprocess.call(xml_gen_cmd, shell=True)

    # Send an HTTP GET request to the URL
    response = requests.get(html)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Get the content from the response
        html_content = response.text

        input_file = f"{out_dir}/input.htm"

        # Specify the name of the file where you want to save the content
        output_file = f"{out_dir}/{Path(html).stem}.htm"

        # Write the content to a local file
        with open(input_file, "w") as file:
            file.write(html_content)

        # add DataTypes tags to tagged elements
        soup = add_datatype_tags(html_content, html_elements, output_file)

        div_element = soup.new_tag("div", style="display: none")
        ix_header = generate_ix_header(file_id=file_id, filename=filename)
        div_element.append(BeautifulSoup(ix_header, "xml"))

        try:
            body = soup.body

            # Find the head tag
            head_tag = soup.head

            # Create a new meta tag
            meta_tag = soup.new_tag("meta")
            meta_tag.attrs["http-equiv"] = "Content-Type"
            meta_tag.attrs["content"] = "text/html"

            # Insert the meta tag into the head tag
            head_tag.insert(0, meta_tag)

            # Insert the div element as the first child of the body
            body.insert(0, div_element)
        except Exception as e:
            print("Body Element Not fount")

        prettified_html = soup.prettify("ascii", formatter="html")

        with open(output_file, "wb") as out_file:
            xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
            xml_declaration_bytes = xml_declaration.encode("utf-8")

            # out_file.write('<?xml version="1.0" encoding="utf-8"?>\n')

            out_file.write(xml_declaration_bytes)
            # Convert to bytes with UTF-8 encoding
            out_file.write(prettified_html)

        with open(output_file, "r", encoding="utf-8") as f:
            html_content = f.read()

            html_content = remove_ix_namespaces(html_content)
            html_attributes = add_html_attributes()
            html_attributes = str(html_attributes).replace("</html>", "")
            # Find all occurrences of &nbsp; in the HTML document
            # Replace each occurrence with &#160;
            html_content = (
                html_content.replace("&nbsp;", "&#160;")
                .replace("&rsquo;", "&#180;")
                .replace("&sect;", "&#167;")
                .replace("&ndash;", "&#8211;")
                .replace("&ldquo;", "&#8220;")
                .replace("&rdquo;", "&#8221;")
                .replace("<font", "<span")
                .replace("</font>", "</span>")
                .replace("<html>", html_attributes)
            )
            with open(output_file, "w", encoding="utf-8") as output_file:
                output_file.write(html_content)

        # add comments to generated xml files
        generate_xml_comments(out_dir)

    return redirect(url_for("ixbrl_viewer_file_generation", file_path=out_dir))


@app.route("/api/html", methods=["GET", "POST"])
def read_html_tagging_file():
    file_id = request.json.get("file_id")
    record = get_db_record(file_id=file_id)
    extra = record.get("extra", None)
    if extra is not None:
        html_file = extra.get("url")
        url_path = Path(html_file)
        filename = get_filename(html_file)
        # Use the name attribute to get the file name
        file_name = f"{url_path.stem}.xlsx"
        xlsx_file = f"{storage_dir}/{Path(html_file).stem}/DTS/{file_name}"
        xlsx_file_store_loc = f"{storage_dir}/{Path(html_file).stem}/DTS/"
        html_elements = extract_html_elements(html_file)
        DTS, concepts = initialize_concepts_dts(filename)
        add_html_elements_to_concept(html_elements, concepts, DTS)
        generate_concepts_dts_sheet(xlsx_file, xlsx_file_store_loc, concepts, DTS)
        return redirect(
            url_for(
                "generate_xml_files",
                file_id=file_id,
                html=html_file,
                xlsx=file_name,
            )
        )
    else:
        return {"error": "html file Not found"}, 400


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
    # with open("output.json", "w") as output:
    #     output.write(json.dumps(data))

    # # read json data from data.json file
    # with open("data.json", "r") as file:
    #     data = json.load(file)

    args = data, ticker, filing_date, company_website, client_id
    # Initialize XMLGenerators and generate the pre.xml file.
    xsd_generator = XSDGenerator(*args)
    xsd_generator.generate_xsd_schema()

    args = data, filing_date, ticker, company_website, client_id
    pre_generator = PreXMLGenerator(*args)
    pre_generator.generate_pre_xml()

    args = data, ticker, filing_date, company_website, client_id
    def_generator = DefXMLGenerator(*args)
    def_generator.generate_def_xml()

    args = data, filing_date, ticker, company_website, client_id
    cal_generator = CalXMLGenerator(*args)
    cal_generator.generate_cal_xml()

    args = data, filing_date, ticker, company_website, client_id
    lab_generator = LabXMLGenerator(*args)
    lab_generator.generate_lab_xml()

    # generate xHTML file
    args = data, filing_date, ticker, cik, file_id, html_file, split_file
    xhtml_generator = XHTMLGenerator(*args)
    xhtml_generator.generate_xhtml_file()

    file_path = f"data/{ticker}-{filing_date}"

    ixbrl_package_url, ixbrl_file_url, log_file_url = ixbrl_viewer_file_generation(
        file_path
    )

    return {
        "messages": "XML Files generated successfully.",
        "ixbrl_package_url": ixbrl_package_url,
        "ixbrl_file_url": ixbrl_file_url,
        "log_file_url": log_file_url,
    }


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

    images = read_images_from_folder(output_folder)

    bucket_name = config("AWS_S3_BUCKET_NAME")
    for filename, img_path in images:
        uploaded_url = upload_image_to_s3(img_path, bucket_name, filename)
        uploaded_images[filename] = uploaded_url

    for filename in os.listdir(output_folder):
        if filename.endswith((".htm", ".html")):
            input_html_file = os.path.join(output_folder, filename)

            with open(input_html_file, "r") as html_file:
                soup = BeautifulSoup(html_file, "html.parser")
                img_tags = soup.find_all("img")
                for img in img_tags:
                    img_url = img["src"]
                    # Assuming img_url is a relative path, construct S3 URL
                    s3_url = uploaded_images.get(img_url)
                    img["src"] = s3_url

            # Save modified HTML back
            with open(input_html_file, "w") as modified_html:
                modified_html.write(str(soup))

            try:
                # Read the file content into memory
                with open(input_html_file, "rb") as f:
                    file_content = f.read()

                # Convert the file content to BytesIO
                file_object = io.BytesIO(file_content)

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
