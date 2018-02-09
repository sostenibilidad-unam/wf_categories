#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request, send_from_directory
from werkzeug import secure_filename
import shapefile
from jinja2 import Environment, FileSystemLoader
import json

import hashlib
from json import dumps

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = './uploads/'

ALLOWED_EXTENSIONS = ['prj', 'shp', 'dbf', 'shx']

env = Environment(loader=FileSystemLoader('templates'))

@app.route('/wf_categories/<map_id>')
def table(map_id):
    if map_id == "nada":
        layer_url = "/static/test.json"
        
    else:
        layer_url = "/uploads/%s/layer.json" % map_id
        
    template = env.get_template('base.html')
    return template.render(layer_url=layer_url)


@app.route('/uploads/<path:path>')
def serve_uploads(path):
    return send_from_directory('uploads', path)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_from_shp(shp_path):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

    md5 = hashlib.md5()
    
    with open(shp_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    
    
    return md5.hexdigest()

@app.route('/wf_categories/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    elShp = ""
    ######################################################################################## falta un chek de que viene el shp, shx, prj y dbf
    for f in uploaded_files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if f.filename.endswith(".shp"):
                elShp = f.filename
            filenames.append(filename)
    print os.path.join(app.config['UPLOAD_FOLDER'], elShp)      
    reader = shapefile.Reader(os.path.join(app.config['UPLOAD_FOLDER'], elShp))
    print reader.shapeType
    fields = reader.fields[1:]
    field_names = [field[0] for field in fields]
    buff = []
    for sr in reader.shapeRecords():
        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        buff.append(dict(type="Feature", \
         geometry=geom, properties=atr)) 
    
    el_hash = hash_from_shp(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "dbf"))
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], el_hash)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "dbf"))
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "prj"))
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "shp"))
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "shx"))
        return redirect("/parallel_coordinates_maps/%s" % el_hash)
    else:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], el_hash))
    
    # write the GeoJSON file
    with open(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], el_hash), "layer.json"), "w") as geojson:
        geojson.write(dumps({"type": "FeatureCollection", "features": buff}, indent=0))
    
        
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "dbf"))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "prj"))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "shp"))
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], elShp[:-3] + "shx"))
    return redirect("/wf_categories/%s" % el_hash)




if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5004,
        debug=True
    )


