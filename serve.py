#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from flask import Flask, make_response, render_template, jsonify, redirect, url_for, request, send_from_directory
from werkzeug.utils import secure_filename
import shapefile
from jinja2 import Environment, FileSystemLoader

import matplotlib

matplotlib.use("Agg")


from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import matplotlib.pyplot as plt
from matplotlib import colors
from io import BytesIO
import numpy

import hashlib
from json import dumps

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = '/var/www/wf_categories/uploads/'

ALLOWED_EXTENSIONS = ['prj', 'shp', 'dbf', 'shx']

env = Environment(loader=FileSystemLoader('templates'))

@app.route("/")
def root():
    return redirect('/wf_categories/df', code=302)

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

#@app.route('/static/<path:path>')
#def serve_static(path):
#    return send_from_directory('static', path)


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

def bojorquezSerrano(fp, categories=5, maximum=1.0, minimum=0.0):
    the_sum = 0
    for i in range(categories):
        the_sum += ((fp) ** i)

    bit = (maximum - minimum) / the_sum
    cuts = []
    cuts.append(minimum)
    for i in range(categories-1):
        prev = cuts[i]
        cut = prev + fp ** i * bit
        cuts.append(cut)
    cuts.append(maximum)
    return cuts


def wf(t, fp, min_v, max_v):
    x_cuts = bojorquezSerrano(fp, minimum=min_v, maximum=max_v)
    if t < x_cuts[1]:
        return 0.2
    elif t >= x_cuts[1] and t < x_cuts[2]:
        return 0.4
    elif t >= x_cuts[2] and t < x_cuts[3]:
        return 0.6
    elif t >= x_cuts[3] and t < x_cuts[4]:
        return 0.8
    elif t >= x_cuts[4]:
        return 1.0


@app.route("/color_bar/")
def color_bar():
    fp = float(request.args.get('fp', 2))
    min_v = float(request.args.get('min', 0))
    max_v = float(request.args.get('max', 1))
#    value = float(request.args.get('value', -1))
#    value_index = int(99 * ((value - min_v)/(max_v - min_v)))
    x = numpy.linspace(min_v, max_v, 100)  # 100 linearly spaced numbers
    y = [wf(t, fp, min_v=min_v, max_v=max_v) for t in x]

    fig = Figure(figsize=(7, 1))
    grid = plt.GridSpec(1, 1, hspace=0)
#
#    ax = fig.add_subplot(grid[0:7, 0])
#
#
#    ax.plot(x, y)
    cmap = colors.LinearSegmentedColormap.from_list("",
                                                    ["#4ABEB5", "#10005A"],
                                                    N=5)
    ax = fig.add_subplot(grid[0, 0])
    espesor = (max_v - min_v) / 11.0
    ax.imshow([y, y], cmap=cmap, extent=[min_v, max_v, 0, espesor])
    #ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    fig.tight_layout()
    canvas = FigureCanvas(fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response





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
    print(os.path.join(app.config['UPLOAD_FOLDER'], elShp))
    reader = shapefile.Reader(os.path.join(app.config['UPLOAD_FOLDER'], elShp))
    print(reader.shapeType)
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
        return redirect("/wf_categories/%s" % el_hash)
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
