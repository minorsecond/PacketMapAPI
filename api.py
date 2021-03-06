from flask import Flask, render_template
from flask_restful import Resource, Api
from flask_jsonpify import jsonify
from sqlalchemy import create_engine
import configparser

config = configparser.ConfigParser()
config.read("settings.cfg")

pg_user = config['postgres']['username']
pg_pw = config['postgres']['password']
remote_pg_host = config['postgres']['remote_pg_host']
pg_db = config['postgres']['db']
pg_port = config['postgres']['port']

app = Flask(__name__)
api = Api(app)

con_string = f"postgresql://{pg_user}:{pg_pw}@" \
             f"{remote_pg_host}/{pg_db}"

remote_engine = create_engine(con_string)


@app.route("/api")
def hello():
    return "<h1 style='color:Black; text-align: center;'>" \
           "Packet Radio Map API</h1>" \
           "<BR>" \
           "The Packet Radio Map data are available in JSON format and " \
           "consist of spatial & non-spatial components. Operators and " \
           "digipeaters come with spatial X (Longitude) and Y (Latitude) " \
           "data, contained in a tuple (e.g. (x, y)). The coordinate system " \
           " (SRS) is EPSG:4326. All timestamps are given in the format " \
           "YYYY-MM-DD HH:MM:SS in the UTC timezone.  Timestamps are " \
           "24-hour time." \
           "<BR><BR>" \
           "The data are updated " \
           "once every half hour at a random time (when the nodes are " \
           "scanned)." \
           "<BR><BR>" \
           "The Denver area data are taken directly from my radio's MHeard " \
           "list and are updated every 15 minutes. All Denver data is on 2m " \
           "145.050 Mhz." \
           "<ul>" \
           "<li><a href='/api/mheard'>MHeard Data</a></li>" \
           "  <ul>" \
           "    <li>Parent ID - The node that received the transmission</li>" \
           "    <li>Call - The transmitting station</li>" \
           "    <li>Heard Time - The time that the transmission was received in UTC timezone</li>" \
           "    <li>SSID - The SSID of the transmitting station, if any</li>" \
           "    <li>Band - The band the transmission was heard on</li>" \
           "  </ul>" \
           "<li><a href='/api/operators'>Operator Data</a></li>" \
           "  <ul>" \
           "    <li>Parent ID - The last node that heard the operator</li>" \
           "    <li>Call - The station call</li>" \
           "    <li>Last Heard - The last time the station was received in UTC timezone</li>" \
           "    <li>Grid - The station's Maidenhead grid square</li>" \
           "    <li>Coordinates - The X & Y coordinates of the station</li>" \
           "    <li>Bands - Bands that the station has been heard on</li>" \
           "  </ul>" \
           "<li><a href='/api/digipeaters'>Digipeater Data</a></li>" \
           "  <ul>" \
           "    <li>Call - The digipeater callsign</li>" \
           "    <li>Last Heard - The last time the digipeater was received in UTC timezone</li>" \
           "    <li>Grid - The digipeater's Maidenhead grid square</li>" \
           "    <li>SSID - The digipeater's SSID</li>" \
           "    <li>Coordinates - The X & Y coordinates of the digiepater</li>" \
           "  </ul>" \
           "<li><a href='/api/nodes'>Node Data</a></li>" \
           "  <ul>" \
           "    <li>Call - The NET/ROM node callsign</li>" \
           "    <li>Grid - The NET/ROM node Maidenhead grid square</li>" \
           "    <li>Coordinates - The NET/ROM node X & Y coordinates</li>" \
           "  </ul>" \
           "<li><a href='/api/denver_mheard'>Denver area MHeard list (RF)</a></li>" \
           "  <ul>" \
           "    <li>Call - The transmitting operator's callsign</li>" \
           "    <li>SSID - The transmitting operator's SSID</li>" \
           "    <li>Heard Time - The time that the transmission was received in UTC timezone</li>" \
           "  </ul>" \
           "<li><a href='/api/denver_operators'>Denver area operators (RF)</a></li>" \
           "  <ul>" \
           "    <li>Call - The operator's callsign</li>" \
           "    <li>Last Heard - The last time the station was received in UTC timezone</li>" \
           "    <li>Coordinates - The X & Y coordinates of the station</li>" \
           "  </ul>" \
           "<li><a href='/api/denver_digipeaters'>Denver area digipeaters (RF)</a></li>" \
           "  <ul>" \
           "    <li>Call - The digipeater's callsign</li>" \
           "    <li>Last Heard - The last time the digipeater was received in UTC timezone</li>" \
           "    <li>Grid - The digipeater Maidenhead grid square</li>" \
           "    <li>SSID - The digipeater's SSID</li>" \
           "    <li>Coordinates - The digipeater's X & Y coordinates</li>" \
           "  </ul>" \
           "</ul>"


class RemoteMH(Resource):
    """
    Remote MHeard list API
    """
    def get(self):
        conn = remote_engine.connect()
        query = conn.execute("select parent_call, "
                             "split_part(remote_call, '-', 1), "
                             "coalesce(to_char(heard_time, "
                             "'YYYY-MM-DD HH24:MI:SS'), 'NULL'),"
                             " ssid, band "
                             "from remote_mh "
                             "order by heard_time desc")

        result = {'mheard': [i for i in query.cursor.fetchall()]}
        return jsonify(result)


class DenverMH(Resource):
    """
    Denver area MHeard list API
    """
    def get(self):
        conn = remote_engine.connect()
        query = conn.execute("select op_call, ssid,"
                             "coalesce(to_char(timestamp, "
                             "'YYYY-MM-DD HH24:MI:SS'), 'NULL') "
                             "from mh_list "
                             "order by timestamp desc")

        result = {'denver_mheard': [i for i in query.cursor.fetchall()]}
        return jsonify(result)


class RemoteOperators(Resource):
    """
    Remote operators API
    """
    def get(self):
        conn = remote_engine.connect()
        query = conn.execute("select parent_call, remote_call, "
                             "coalesce(to_char(lastheard, "
                             "'YYYY-MM-DD HH24:MI:SS'), 'NULL'), "
                             "grid, (st_x(geom), st_y(geom)), bands "
                             "from remote_operators "
                             "order by lastheard desc")
        result = {'operators': [i for i in query.cursor.fetchall()]}
        return jsonify(result)


class DenverOperators(Resource):
    """
    Denver area operators API
    """
    def get(self):
        conn = remote_engine.connect()
        query = conn.execute("select call, "
                             "coalesce(to_char(lastheard, "
                             "'YYYY-MM-DD HH24:MI:SS'), 'NULL'), "
                             "grid, (st_x(geom), st_y(geom)) "
                             "from operators "
                             "order by lastheard desc")
        result = {'operators': [i for i in query.cursor.fetchall()]}
        return jsonify(result)


class RemoteDigipeaters(Resource):
    """
    Remote digipeaters API
    """
    def get(self):
        conn = remote_engine.connect()
        query = conn.execute("select call, "
                             "coalesce(to_char(lastheard, "
                             "'YYYY-MM-DD HH24:MI:SS'), 'NULL'), grid, ssid, "
                             "(st_x(geom), "
                             "st_y(geom)) from remote_digipeaters "
                             "order by lastheard desc")
        result = {'digipeaters': [i for i in query.cursor.fetchall()]}
        return jsonify(result)


class DenverDigipeaters(Resource):
    """
    Denver digipeaters API
    """
    def get(self):
        conn = remote_engine.connect()
        query = conn.execute("select call, coalesce(to_char(lastheard,"
                             "'YYYY-MM-DD HH24:MI:SS'), 'NULL'), grid, ssid, "
                             "(st_x(geom), st_y(geom)) "
                             "from digipeaters")
        result = {'denver_digipeaters': [i for i in query.cursor.fetchall()]}
        return jsonify(result)


class Nodes(Resource):
    """
    NET/ROM nodes API
    """
    def get(self):
        conn = remote_engine.connect()
        query = conn.execute("select call, grid, (st_x(geom), st_y(geom)) "
                             "from nodes "
                             "order by call asc")
        result = {'nodes': [i for i in query.cursor.fetchall()]}
        return jsonify(result)


api.add_resource(RemoteMH, '/api/mheard')
api.add_resource(RemoteOperators, '/api/operators')
api.add_resource(RemoteDigipeaters, '/api/digipeaters')
api.add_resource(Nodes, '/api/nodes')
api.add_resource(DenverMH, '/api/denver_mheard')
api.add_resource(DenverOperators, '/api/denver_operators')
api.add_resource(DenverDigipeaters, '/api/denver_digipeaters')

if __name__ == '__main__':
    app.run()
