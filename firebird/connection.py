import fdb

database = {
    "host": "127.0.0.1",
    "database": "mpass",
    "user": "SYSDBA",
    "password": "masterkey",
}


def con_to_firebird(query, *args):
    con = fdb.connect(**database)
    cur = con.cursor()
    try:
        cur.execute(query, *args)
    except fdb.Error as e:
        print(e)
    else:
        for line in cur.fetchall():
            yield line
    finally:
        con.close()
