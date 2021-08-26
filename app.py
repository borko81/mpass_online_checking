import fdb
from datetime import timedelta, datetime
import json
from flask import Flask, request, jsonify, make_response, session, redirect, flash, url_for
from flask.templating import render_template
# from flask_cors import CORS
from flask.wrappers import Response

from firebird.connection import con_to_firebird
import hashlib


app = Flask(__name__)
app.config["SECRET_KEY"] = "Therion"
# CORS(app)


@app.route("/", methods=["GET"])
def index():
    """
        check user is authenticated or not, if not return to login form
    """
    if not session.get("logged_in"):
        return render_template("login.html")
    else:
        return redirect(url_for("all_in_a_house"))


@app.route("/login", methods=["POST"])
def login():
    user_credential = hashlib.sha256()
    password_credential = hashlib.sha256()
    user_credential.update(request.form["username"].encode('utf-8'))
    password_credential.update(request.form["password"].encode('utf-8'))
    if user_credential.hexdigest() == "694f9239193cd42447a703b48e6759b6c9917587064798bb14ad020a3b3b8539" and password_credential.hexdigest() == "694f9239193cd42447a703b48e6759b6c9917587064798bb14ad020a3b3b8539":
        session.permanent = False
        session["logged_in"] = True
        return redirect(url_for("all_in_a_house"))
    else:
        flash("wrong autentication")
        return index()


@app.route("/logout")
def logout():
    """ Logount function """
    session["logged_in"] = False
    return index()


@app.route('/all_in_a_house')
def all_in_a_house():
    if session.get("logged_in") is True:
        """
        Begin page, show employees in a house
        return: name, datetime in, status
        """
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
    else:
        flash("wrong autentication")
        return index()


@app.route('/data_movements', methods=['POST', 'GET'])
def data_movements():
    """
    Movements employee by first and last datetime.
    return: name, datetime in, status
    """
    if session.get("logged_in") is True:
        if request.method == 'POST':
            # If form send empty date cast for to date today.
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
    else:
        flash("wrong autentication")
        return index()


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
    """
    Employe total time in a house
    """
    if session.get("logged_in") is True:
        return render_template('time_id_the_house.html')
    else:
        flash("wrong autentication")
        return index()


@app.route('/data_time_in_house' , methods=['POST', 'GET'])
def data_time_in_house():
    """
    show return result from total_time
    return: name, total_time in a house, count in and count out, Няма съвпадащи данни if employe has in but not out in custom date period.
    """
    if session.get("logged_in") is True:
        if request.method == 'POST':
            # If form send empty date cast for to date today.
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
            # cikle to calculate needed staff
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
    else:
        flash("wrong autentication")
        return index()


if __name__ == '__main__':
    # Debug is active!!!!!!!!!!!!!!!!!!!
    app.run(port=7000, debug=True)
