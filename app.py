from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
from string import ascii_uppercase
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'PUTEVERTYINGYOUWANT'
socketio = SocketIO(app)

rooms = dict()

def generate_unique_room(length):
    while True:
        code = ''
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code


@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('room')
        join = request.form.get('join', False)
        create = request.form.get('create', False)
        if not name:
            return render_template('home.html', error='provide a name.')
        if join != False and not code:
            return render_template('home.html', error='provide a room code.')
        room = code
        if create != False:
            room = generate_unique_room(4)
            rooms[room] = {'members': 0, 'messages': []}
            print(rooms)
        elif room not in rooms:
            return render_template('home.html', error='room does not exist')
        session['name'] = name
        session['room'] = room
        return redirect(url_for('room'))
    return render_template('home.html')


@app.route('/room')
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))
    return render_template('room.html', room=room, messages=rooms[room]['messages'])


@socketio.on('message')
def message(data):
    room = session.get('room')
    name = session.get('name')
    if room not in rooms:
        return
    content = {"name": name, "message": data['data'], 'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    send(content, to=room)
    rooms[room]['messages'].append(content)


@socketio.on('connect')
def connect(auth):
    room = session.get('room')
    name = session.get('name')
    if not name or not room:
        return
    if room not in rooms:
        leave_room(room)
        return
    join_room(room)
    send({"name": name, "message": "has entered the room", 'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, to=room)
    rooms[room]['members'] += 1

    
@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')
    leave_room(room)
    if room in rooms:
        rooms[room]['members'] -= 1
        if rooms[room]['members'] <= 0:
            del rooms[room]
    send({"name": name, "message": "has left the room", 'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
    
