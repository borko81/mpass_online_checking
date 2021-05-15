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


def calculate_time(info_time_list):
    total_time = info_time_list.pop()
    seconds = 0
    while info_time_list:
        temp = (total_time - info_time_list.pop()).seconds
        seconds += temp
        try:
            total_time = info_time_list.pop()
        except IndexError:
            pass
    return str(timedelta(seconds=seconds))


@app.route('/show_total_time', methods=['POST', 'GET'])
def total_time():
    return render_template('time_id_the_house.html')


@app.route('/data_time_in_house' , methods=['POST', 'GET'])
def data_time_in_house():
    if request.method == 'POST':
        f_data = request.form["f_date"] or str(datetime.today().date())
        l_data = request.form["l_date"] or str(datetime.today().date())
        query = """
        select
        employees.name,
        pass.datetime,
        pass.passtype
        from pass
        inner join employees on employees.id = pass.emp_id
        where cast(pass.datetime as date) between ? and ?
        order by 1, 2
        """
        result = {}
        data = con_to_firebird(query, (f_data, l_data))
        for line in data:
            name = line[0]
            time_check = line[1]
            passtype = line[2]
            if name not in result:
                result[name] = {'in': 0, 'out': 0, 'total_time': []}
            if passtype == '1':
                result[name]['in'] += 1
            else:
                result[name]['out'] += 1
            result[name]['total_time'].append(time_check)

        for _, value in result.items():
            if value['out'] == value['in']:
                value['total_time'] = calculate_time(value['total_time'])
            else:
                value['total_time'] = 'Няма съвпадащи данни'
        return render_template('time_id_the_house.html', data=result)
    message = {'greeting': 'Must enter through form'}
    return message  # serialize and use JSON headers


if __name__ == '__main__':
    app.run(debug=True)
