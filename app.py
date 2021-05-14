import fdb
from datetime import timedelta, datetime
import json
from flask import Flask, request, jsonify, make_response
from flask.templating import render_template
from flask_cors import CORS
from flask.wrappers import Response

from firebird.connection import con_to_firebird

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    query = """
    select
    pass.emp_id as p_id,
    employees.name,
    pass.datetime,
    case when pass.passtype = 1 then 'Влиза'
    else 'Излиза'
    end
    from pass
    inner join employees on employees.id = pass.emp_id
    inner join pass_node on pass_node.in_id = pass.id
    and exists(
        select pass_node.out_id from pass_node where pass.id = pass_node.in_id
        and pass_node.out_id is null
    )
    order by 2, 3
    """
    fdb_data = con_to_firebird(query)
    return render_template('employee_in_house.html', data=fdb_data)


@app.route('/data_movements', methods=['POST', 'GET'])
def data_movements():
    if request.method == 'POST':
        f_data = request.form["f_date"] or str(datetime.today().date())
        l_data = request.form["l_date"] or str(datetime.today().date())
        query = """
        select
        employees.name,
        pass.datetime,
        case when pass.passtype = 1 then 'Влиза'
        else 'Излиза'
        end
        from pass
        inner join employees on employees.id = pass.emp_id
        where cast(datetime as date) between ? and ?
        order by 1, 2
        """
        data = con_to_firebird(query, (f_data, l_data))
        return render_template('employee_movement.html', data=data)

    message = {'greeting': 'Must enter through form'}
    return message  # serialize and use JSON headers


@app.route('/show_movement', methods=['POST', 'GET'])
def movements():
    return render_template('employee_movement.html')


if __name__ == '__main__':
    app.run(debug=True)
