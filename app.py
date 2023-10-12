import boto3
import subprocess
import pandas as pd
import io, os, requests
from pathlib import Path
from decouple import config
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from utils import (
    extract_html_elements,
    add_html_elements_to_concept,
    generate_concepts_dts_sheet,
    generate_ix_header,get_db_record,
    update_db_record,
    initialize_concepts_dts,
    get_filename
)
from threading import Thread
# from auto_tagging.tagging import auto_tagging
from flask import Flask, request, redirect, url_for


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

    return file


def get_validation_logs(file):
    logs_html = f"{storage_dir}/{file}/out/RenderingLogs.htm"
    with open(logs_html, "r", encoding="utf-8") as file:
        html_content = file.read()
        try:
            logs_df = pd.read_html(html_content)[0]
            return logs_df.to_dict()
        except:
            return {"message": "logs not found"}


def s3_uploader(name, body):
    # name is s3 file name
    # boyd is io.BytesIO()
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
    s3.Bucket(bucket).put_object(
        Key=name,
        Body=body.getvalue(),
        ACL="public-read",
        ContentType="application/octet-stream",
    )
    location = session.client("s3").get_bucket_location(Bucket=bucket)[
        "LocationConstraint"
    ]
    uploaded_url = f"https://s3-{location}.amazonaws.com/{bucket}/{name}"
    return uploaded_url


@app.route("/")
def index():
    return {"message": "welcome to ixbrl viewer"}


@app.route("/api/validation")
def validation():
    query_params = request.args
    url = query_params.get("q", None)
    if url is None:
        return {"message": "query params required."}

    file = download_files(url)

    # validation process
    file = file
    plugin = f"{base_dir}/EdgarRenderer"

    print("\n===============[validation started]===============\n")

    validation_cmd = f"python arelleCmdLine.py -f {file} --plugins {plugin} --disclosureSystem efm-pragmatic --validate -r out"
    subprocess.call(validation_cmd, shell=True)
    # get logs
    response = get_validation_logs(file)
    return response


@app.route("/api/ixbrl-viewer")
def ixbrl_viewer_file_generation():
    file = request.args.get("file_path", None)

    # create viewer folder
    Path(f"{file}/viewer").mkdir(parents=True, exist_ok=True)

    # ixbrl-file-generation
    plugin = f"{base_dir}/ixbrl-viewer/iXBRLViewerPlugin"
    output_html = f"{file}/viewer/{Path(file).name}-ixbrl-report-viewer.html"
    viewer_url = "https://cdn.jsdelivr.net/npm/ixbrl-viewer/iXBRLViewerPlugin/viewer/dist/ixbrlviewer.js"

    print("\n===============[ixbrl viewer file generation started]===============\n")

    ixbrl_file_gen_cmd = f"python arelleCmdLine.py --plugins={plugin} -f {file} --save-viewer {output_html} --viewer-url {viewer_url}"
    subprocess.call(ixbrl_file_gen_cmd, shell=True)
    try:
        with open(output_html, "rb") as file:
            body = io.BytesIO(file.read())
            # Parse the URL to extract the path
            parsed_url = urlsplit(output_html)
            # Get the filename from the path using pathlib
            path = Path(parsed_url.path)
            filename = path.name
            url = s3_uploader(name=filename, body=body)
            return {"ixbrl_file": url}
    except Exception as e:
        return {"error": "ixbrl file is not generated"}, 400




@app.route("/api/xml-files")
def generate_xml_files():
    html = request.args.get("html", None)
    xlsx = request.args.get("xlsx", None)
    file_id = request.args.get("file_id", None)

    filepath = f"{storage_dir}/DTS/{xlsx}"
    out_dir = f"{storage_dir}/{Path(html).stem}"
    filename = get_filename(html)

    print("\n===============[loadFromExcel started]===============\n")

    xml_gen_cmd = f"python arelleCmdLine.py -f {filepath} --plugins loadFromExcel --save-Excel-DTS-directory={out_dir}"
    subprocess.call(xml_gen_cmd, shell=True)

    # Send an HTTP GET request to the URL
    response = requests.get(html)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Get the content from the response
        html_content = response.text

        # Specify the name of the file where you want to save the content
        file_name = f"{out_dir}/{Path(html).stem}.htm"

        # Write the content to a local file
        with open(file_name, "w") as file:

            soup = BeautifulSoup(html_content, 'html.parser')
            # Create a temp div element
            div_element = soup.new_tag('div', style="display: none")
            ix_header = generate_ix_header(file_id=file_id, filename=filename)
            div_element.append(BeautifulSoup(ix_header, 'html.parser'))

            body = soup.body
            # Insert the div element as the first child of the body
            body.insert(0, div_element)

            # Convert the modified soup object back to a string
            modified_html = str(soup.prettify())
            file.write(modified_html)

    return redirect(url_for("ixbrl_viewer_file_generation", file_path=out_dir))


@app.route("/api/html", methods=["GET", "POST"])
def read_html_tagging_file():

    file_id = request.json.get("file_id")
    record = get_db_record(file_id = file_id)
    extra = record.get("extra", None)
    if extra is not None:
        html_file = extra.get("url")
        url_path = Path(html_file)
        filename = get_filename(html_file)
        # Use the name attribute to get the file name
        file_name = f"{url_path.stem}.xlsx"
        xlsx_file = f"{storage_dir}/DTS/{file_name}"
        html_elements = extract_html_elements(html_file)
        DTS, concepts = initialize_concepts_dts(filename)
        add_html_elements_to_concept(html_elements, concepts)
        generate_concepts_dts_sheet(xlsx_file, concepts, DTS)
        return redirect(url_for("generate_xml_files", file_id = file_id, html=html_file, xlsx=file_name))
    else:
        return {"error":"html file Not found"}, 400
    
@app.route("/api/auto-tagging", methods=["POST"])
def auto_tagging_view():
    file_id = request.json.get("file_id", None)
    url = config("AUTO_TAGGING_URL")
    response = requests.post(url, json={'file_id': file_id})
    return response.json() , response.status_code

if __name__ == "__main__":
    port = config("PORT")
    app.run(host="0.0.0.0", port=port, debug=True)
