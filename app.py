from flask import Flask, request, render_template, redirect, url_for, session
import psycopg2
import base64
import datetime

app = Flask(__name__)
app.secret_key = 'k29_super_secret_key'


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="k29photo",
        user="postgres",
        password=""  # DB password
    )

# Τα παρακάτω σχόλια που σχετίζονται με την ανάκτηση των δεδομένων των φωτογραφίων ισχύουν και 
# για τις υπόλοιπες περιπτώσεις που αντλούμε φωτογραφίες από τη βάση, όπως π.χ. στην αναζήτηση από ετικέτες
@app.route('/')
def home():
    current_user = session.get('user_id')
    view_mode = request.args.get('view', 'all')

    if view_mode == 'mine' and not current_user:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Επιστρέφονται οι φωτογραφίες του χρήστη (αν είναι συνδεδεμένος)
    if view_mode == 'mine':
        query = """SELECT P."Photo-id", P."Data", P."Caption"
                   FROM "Photos" P
                            JOIN "Albums" A ON P."Album-id" = A."Album-id"
                   WHERE A."User-id" = %s
                   LIMIT 10"""
        cur.execute(query, (current_user,))
    else:
        #Επιστρέφονται φωτογραφίες όλων των χρηστών
        query = """SELECT "Photo-id", "Data", "Caption"
                   FROM "Photos"
                   LIMIT 10"""
        cur.execute(query)

    # Φέρνουμε τα δεδομένα από το SQL ερώτημα
    rows = cur.fetchall()
    # Δημιουργία κενής λίστας όπου θα αποθηκεύσουμε τις φωτογραφίες με τα σχόλιά τους κτλ
    photo_list = []
    for row in rows:
        photo_id = row[0]
        # Βάζουμε αρχικά none για να μη βρεθούμε προ εκπλήξεων αν δεν υπάρχουν τα δεδομένα αρχείου της φωτογραφίας
        photo_src = None
        # Εδώ ελέγχουμε αν υπάρχουν τα δεδομένα αρχείου της φωτογραφίας και αν η συνθήκη είναι αληθής, τότε 
        # τα μετατρέπουμε σε μορφή που μπορεί να εμφανιστεί στο HTML (base64)
        if row[1]:
            img_data = bytes(row[1])
            photo_src = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"

        # Εδώ φέρνουμε τις ετικέτες που συνοδεύουν την φωτογραφία που ελέγχεται από το for
        cur.execute('SELECT TP."Title" FROM "Photos_has_Tags" TP WHERE TP."Photo-id" = %s', (photo_id,))
        tags_data = cur.fetchall()
        tags_list = [t[0] for t in tags_data]

        # Εδώ φέρνουμε τα σχόλια που συνοδεύουν την φωτογραφία που ελέγχεται από το for
        cur.execute('''SELECT "User-id", "Comment_text", "Post_date"
                       FROM "Comments"
                       WHERE "Photo-id" = %s
                       ORDER BY "Post_date" ASC''', (photo_id,))
        comments_data = cur.fetchall()
        comments_list = [{'user_id': c[0] if c[0] else 'Επισκέπτης', 'text': c[1], 'date': c[2]} for c in comments_data]

        # Βρίσκουμε ποιοι έχουν κάνει like στην φωτογραφία που ελέγχεται από το for
        cur.execute('''SELECT u."User-id"
                       FROM "Likes" l
                                JOIN "Users" u ON l."User-id" = u."User-id"
                       WHERE l."Photo-id" = %s''', (photo_id,))
        # Παίρνουμε τα user-id των χρηστών που έχουν κάνει like και τα βάζουμε σε μια λίστα
        likers = [l[0] for l in cur.fetchall()]
        # Μετράμε πόσα like έχει η φωτογραφία που ελέγχεται από το for μετρώντας τα user-id που έχουμε στη λίστα
        likes_count = len(likers)

        # Ελέγχουμε αν ο χρήστης (συνδεδεμένος) έχει κάνει like στη φωτογραφία που ελέχεται από το for και αρχικοποιούμε
        # με false, ότι δεν έχει κάνει like.
        user_has_liked = False
        if current_user:
            cur.execute('''SELECT 1
                           FROM "Likes"
                           WHERE "Photo-id" = %s
                             AND "User-id" = %s''', (photo_id, current_user))
            # Αν έχει κάνει like, αλλάζει η λογική τιμή της παρακάτω μεταβλητής
            if cur.fetchone():
                user_has_liked = True

        # Τέλος, φέρνουμε όλα τα δεδομένα που έχουμε μαζέψει για τη φωτογραφία που ελέγχεται από το for
        photo_list.append({
            'Photo-id': photo_id,
            'Data': photo_src,
            'Caption': row[2],
            'Tags': tags_list,
            'Comments': comments_list,
            'LikesCount': likes_count,
            'Likers': likers,
            'UserHasLiked': user_has_liked
        })

    # Φέρνουμε τα άλμπουμ του χρήστη (αν είναι συνδεδεμένος) για να τα εμφανίσουμε στο dropdown με τα άλμπουμ κατά το ανέβασμα φωτογραφίας
    user_albums = []
    if current_user:
        cur.execute('SELECT "Album-id", "Title" FROM "Albums" WHERE "User-id" = %s', (current_user,))
        for r in cur.fetchall():
            user_albums.append({'album_id': r[0], 'title': r[1]})

    cur.close()
    conn.close()

    return render_template('home.html', photos=photo_list, current_user=current_user, view_mode=view_mode,
                           user_albums=user_albums)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT "User-id" FROM "Users" WHERE "Email" = %s AND "Password" = %s', (email, password))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect(url_for('home'))
        else:
            error = "Wrong email or password"

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/upload_album', methods=['POST'])
def upload_album():
    user_id = session.get('user_id')
    title = request.form.get('title')

    if not title or not user_id:
        return "Λείπει ο τίτλος ή δεν είσαι συνδεδεμένος!"

    conn = get_db_connection()
    cur = conn.cursor()

    # Δεν κοιτάμε εδώ αν υπάρχει ήδη το άλμπουμ Α για τον χρήστη Χ καθώς
    # βάλαμε unique τον συνδυασμό (user-id, title)
    try:
        creation_date = datetime.datetime.now().strftime('%Y-%m-%d')
        # Δεν περνάμε "Album-id", το φτιάχνει η βάση μόνη της
        cur.execute('''
                    INSERT INTO "Albums" ("User-id", "Title", "Creation_date")
                    VALUES (%s, %s, %s)
                    ''', (user_id, title, creation_date))
        conn.commit()
        return redirect(url_for('home'))
    except Exception as e:
        conn.rollback()
        return f"Σφάλμα κατά το ανέβασμα άλμπουμ: {e}"
    finally:
        cur.close()
        conn.close()


@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    user_id = session.get('user_id')
    caption = request.form.get('caption')
    file = request.files.get('photo_file')
    album_title = request.form.get('album_title')

    if not file or not user_id:
        return "Λείπει το αρχείο ή δεν είσαι συνδεδεμένος!"

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT "Album-id"
                    FROM "Albums"
                    WHERE "User-id" = %s
                      AND "Title" = %s
                    ''', (user_id, album_title))

        album_row = cur.fetchone()

        if album_row:
            album_id = album_row[0]
        else:
            return "Σφάλμα: Το album που επέλεξες δεν βρέθηκε!"

        img_binary = file.read()

        # RETURNING για να πάρουμε πίσω το αυτόματο Photo-id
        cur.execute('''
                    INSERT INTO "Photos" ("Data", "Caption", "Album-id")
                    VALUES (%s, %s, %s)
                    RETURNING "Photo-id"
                    ''', (psycopg2.Binary(img_binary), caption, album_id))
        photo_id = cur.fetchone()[0]

        raw_tags = request.form.get('tags')
        if raw_tags:
            # 1. Αντικαθιστούμε όλα τα κόμματα με κενά
            clean_input = raw_tags.replace(',', ' ')


            tag_list = clean_input.split()

            for raw_tag in tag_list:
                clean_tag = raw_tag.lower().strip()  # Το κάνουμε μικρά και διώχνουμε τυχόν κενά

                if clean_tag:
                    cur.execute('SELECT "Title" FROM "Tags" WHERE "Title" = %s', (clean_tag,))
                    tag_exists = cur.fetchone()

                    if not tag_exists:
                        cur.execute('INSERT INTO "Tags" ("Title") VALUES (%s)', (clean_tag,))

                    cur.execute('''
                                INSERT INTO "Photos_has_Tags" ("Photo-id", "Title")
                                VALUES (%s, %s)
                                ''', (photo_id, clean_tag))

        conn.commit()
        return redirect(url_for('home'))

    except Exception as e:
        conn.rollback()
        return f"Σφάλμα κατά το ανέβασμα: {e}"
    finally:
        cur.close()
        conn.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['first_name']
        surname = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        sex = request.form['sex']
        dob = request.form.get('dob') or None
        origin = request.form.get('hometown') or None

        file = request.files.get('profile_pic')
        img_binary = file.read() if file else None

        conn = get_db_connection()
        cur = conn.cursor()
        # Πραγματοποιύμε ελέγχους για την μοναδικότητα κάποιων στοιχείων όπως το email, το username
        try:
            cur.execute('SELECT "Email" FROM "Users" WHERE "Email" = %s', (email,))
            if cur.fetchone():
                error = "User with this email already exists!"
                return render_template('register.html', error=error)

            cur.execute('SELECT "User-id" FROM "Users" WHERE "User-id" = %s', (user_id,))
            if cur.fetchone():
                error = "This Username is already taken!"
                return render_template('register.html', error=error)

            # Εφόσον είναι όλα εντάξει με τουσ παραπάνω ελέγχους, καταχωρούμε στη βάση
            cur.execute("""
                        INSERT INTO "Users" ("User-id", "Name", "Surname", "Email", "DOB", "Origin", "Sex", "Password",
                                             "Data")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (user_id, name, surname, email, dob, origin, sex, password,
                              psycopg2.Binary(img_binary) if img_binary else None))

            # Κραττάμε το πότε δημιουργήθηκε ο κάθε χρήστης
            creation_date = datetime.datetime.now().strftime('%Y-%m-%d')

            # Παίρνει αυτόματο αριθμό από τη Βάση
            cur.execute('''
                        INSERT INTO "Albums" ("User-id", "Title", "Creation_date")
                        VALUES (%s, %s, %s)
                        ''', (user_id, 'Ανεβασμένες φωτογραφίες', creation_date))

            conn.commit()
            return redirect(url_for('users'))
        except Exception as e:
            conn.rollback()
            return f"Error: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template('register.html')


@app.route('/users', methods=['GET'])
def users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT "User-id", "Name", "Surname", "Data" FROM "Users"')
    rows = cur.fetchall()

    users_list = []
    for row in rows:
        photo_src = None
        if row[3]:
            img_data = row[3].tobytes() if isinstance(row[3], memoryview) else bytes(row[3])
            photo_src = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"

        users_list.append({
            'user_id': row[0], 'name': row[1], 'surname': row[2], 'photo_src': photo_src
        })
    cur.close()
    conn.close()
    return render_template('users.html', users=users_list, show_add_button=True)


@app.route('/top_users', methods=['GET'])
def top_users():
    conn = get_db_connection()
    cur = conn.cursor()

    # Το ερώτημα για τη συνεισφορά στην ιστοσελίδα βάσει των οδηγιών της εκφώνησης. Το σκορ προκύπτει από 
    # τον αριθμό των φωτογραφιών που έχει ανεβάσει ο χρήστης και τον αριθμό των σχολίων που έχει κάνει σε φωτογραφίες άλλων χρηστών
    query = """SELECT u."User-id",
                      u."Name",
                      (SELECT count(*)
                       FROM "Photos" p
                                JOIN "Albums" a on a."Album-id" = p."Album-id"
                       WHERE u."User-id" = a."User-id")
                          +
                      (SELECT count(*)
                       FROM "Comments" c
                                JOIN "Photos" p ON p."Photo-id" = c."Photo-id"
                                JOIN "Albums" a
                                     ON a."Album-id" = p."Album-id"
                       WHERE c."User-id" = u."User-id"
                         AND a."User-id" != u."User-id") as Total_Contribution
               FROM "Users" u
               ORDER BY Total_Contribution DESC
               LIMIT 10;"""
    cur.execute(query)
    rows = cur.fetchall()
    top_users = []
    for r in rows:
        top_users.append({'user_id': r[0], 'name': r[1], 'score': r[2]})
    cur.close()
    conn.close()
    return render_template('home.html', users=top_users, active_page='leaderboard',current_user= session.get('user_id'))


@app.route('/add_comment', methods=['GET', 'POST'])
def add_comment():
    
    if request.method == 'GET':
        photo_id = request.args.get('photo_id')
        return render_template('comments.html', photo_id=photo_id)

   
    photo_id = request.form['photo_id']
    current_user = session.get('user_id')
    db_user_id = current_user if current_user else None
    comment_text = request.form.get('comment_text')

    if not comment_text or comment_text.strip() == '':
        return "Σφάλμα: Δεν μπορείς να υποβάλλεις κενό σχόλιο!"

    comment_date = datetime.datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''SELECT A."User-id"
                       FROM "Photos" P
                                JOIN "Albums" A ON P."Album-id" = A."Album-id"
                       WHERE P."Photo-id" = %s''', (photo_id,))
        owner_row = cur.fetchone()

        # Σε περίπτωση συνδεδεμένου χρήστη, εξασφαλίζουμε ότι αυτός που αφήνει σχόλιο δεν μπορεί να είναι αυτός που δημοσίεσυε την φωτογραφία
        if owner_row and current_user and str(owner_row[0]) == str(current_user):
            return "Σφάλμα: Δεν επιτρέπεται να σχολιάσεις τη δική σου φωτογραφία!"

        cur.execute(
            'INSERT INTO "Comments" ("Photo-id", "User-id", "Comment_text", "Post_date") VALUES (%s, %s, %s, %s)',
            (photo_id, db_user_id, comment_text, comment_date))
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('home'))


@app.route('/like_photo', methods=['GET', 'POST'])
def like_photo():
    
    if request.method == 'GET':
        photo_id = request.args.get('photo_id')
        return render_template('like.html', photo_id=photo_id)

    
    photo_id = request.form['photo_id']
    user_id = session.get('user_id')

    if not user_id:
        return "Σφάλμα: Πρέπει να είσαι συνδεδεμένος για να κάνεις Like!"

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT 1 FROM "Likes" WHERE "Photo-id" = %s AND "User-id" = %s', (photo_id, user_id))
        already_liked = cur.fetchone()

        if already_liked:
            cur.execute('DELETE FROM "Likes" WHERE "Photo-id" = %s AND "User-id" = %s', (photo_id, user_id))
        else:
            cur.execute('INSERT INTO "Likes" ("Photo-id", "User-id") VALUES (%s, %s)', (photo_id, user_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('home'))


@app.route('/search_albums', methods=['GET'])
def search_albums():
    current_user = session.get('user_id')
    # Ζητάμε το username αυτουνού του χρήστη του οποίου το άλμπουμ θέλουμε να προβάλουμε
    album_owner = request.args.get('user_id')
    album_title = request.args.get('album_title')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Τσεκάρουμε αν υπάρχει ο συνδυασμός username και τίτλου άλμπουμ
        if album_owner and album_title:

            cur.execute('''SELECT P."Photo-id", P."Data", P."Caption"
                        FROM "Photos" P
                            JOIN "Albums" A ON P."Album-id" = A."Album-id"
                        WHERE A."User-id" ILIKE %s AND A."Title" ILIKE %s
                        ''', (album_owner, album_title))

            rows = cur.fetchall()
            # Περίπτωση που το άλμπουμ δε βρέθηκε ή βρέθηκε αλλά άδειο, οπότε και στις δύο περιπτώσεις εμφανίζουμε κατάλληλο μήνυμα στον χρήστη
            if not rows:
                cur.execute('SELECT "Album-id" FROM "Albums" WHERE "User-id" = %s AND "Title" = %s', (album_owner, album_title))
                if not cur.fetchone():
                    return render_template('albums.html', error=f"Δεν βρέθηκε το άλμπουμ '{album_title}' για τον χρήστη '@{album_owner}'. Δοκίμασε ξανά!")
                else:
                    return render_template('albums.html', error=f"Το άλμπουμ '{album_title}' του χρήστη '@{album_owner}' είναι άδειο!")
                photos = []

            else:
                photos = []

                for r in rows:
                    photo_id = r[0]
                    photo_src = None
                    if r[1]:
                        img_data = bytes(r[1])
                        photo_src = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"

                    cur.execute('SELECT "Title" FROM "Photos_has_Tags" WHERE "Photo-id" = %s', (photo_id,))
                    tags_data = cur.fetchall()
                    tags_list = [t[0] for t in tags_data]

                    cur.execute('''SELECT "User-id", "Comment_text", "Post_date"
                                FROM "Comments"
                                WHERE "Photo-id" = %s
                                ORDER BY "Post_date" ASC''', (photo_id,))
                    comments_data = cur.fetchall()
                    comments_list = [{'user_id': c[0] if c[0] else 'Επισκέπτης', 'text': c[1], 'date': c[2]} for c in comments_data]

                    
                    cur.execute('SELECT COUNT(*) FROM "Likes" WHERE "Photo-id" = %s', (photo_id,))
                    likes_count = cur.fetchone()[0]

                    user_has_liked = False
                    
                    if current_user:
                        cur.execute('''SELECT 1
                                    FROM "Likes"
                                    WHERE "Photo-id" = %s
                                        AND "User-id" = %s''', (photo_id, current_user))
                        if cur.fetchone():
                            user_has_liked = True

                    photos.append({
                        'Photo-id': photo_id,
                        'Data': photo_src,
                        'Caption': r[2],
                        'Tags': tags_list,
                        'Comments': comments_list,
                        'LikesCount': likes_count,
                        'UserHasLiked': user_has_liked
                    })

                return render_template('home.html', photos=photos, active_page='search_albums', search_query=f"{album_title} (@{album_owner})", current_user=current_user)
        
        elif album_owner:
            cur.execute('''Select "User-id"
                        From "Users"
                        Where "User-id" ILIKE %s
                       ''', (album_owner,))
            # Περίπτωση που ο χρήστης δεν βρέθηκε
            if not cur.fetchone():
                return render_template('albums.html', error=f"Ο χρήστης '@{album_owner}' δεν βρέθηκε!")
        
            cur.execute('SELECT "Title" FROM "Albums" WHERE "User-id" = %s', (album_owner,))
            album_title = [{'title': r[0]} for r in cur.fetchall()]

            return render_template('albums.html', album_owner=album_owner, album_title=album_title)

        else:
            return render_template('albums.html')
    
    except Exception as e:
        conn.rollback()
        print(f"Σφάλμα στην αναζήτηση άλμπουμ: {e}")
    finally:
        cur.close()
        conn.close()


@app.route('/search_tags', methods=['GET'])
def search_tags():
    raw_tags = request.args.get('tag_name')
    current_user = session.get('user_id')

    if not raw_tags or raw_tags.strip() == '':
        return render_template('tags.html')

    # Αναζητούμε ετικέτες είτε χωρίζοντάς με κενά είτε με κόμματα
    clean_input = raw_tags.replace(',', ' ')
    tag_list = [t.strip().lower() for t in clean_input.split() if t.strip()]

    if not tag_list:
        return render_template('tags.html')

    conn = get_db_connection()
    cur = conn.cursor()


    placeholders = ','.join(['%s'] * len(tag_list))
    # Η διαζευκτική αναζήτηση, βάσει των οδηγιών της εκφώνησης
    query = f"""
        SELECT P."Photo-id", P."Data", P."Caption"
        FROM "Photos" P
        JOIN "Photos_has_Tags" PT ON P."Photo-id" = PT."Photo-id"
        WHERE PT."Title" IN ({placeholders})
        GROUP BY P."Photo-id", P."Data", P."Caption"
        HAVING COUNT(DISTINCT PT."Title") = %s 
    """

    params = tuple(tag_list) + (len(tag_list),)
    cur.execute(query, params)

    rows = cur.fetchall()
    photos = []

    for r in rows:
        photo_id = r[0]
        photo_src = None
        if r[1]:
            img_data = bytes(r[1])
            photo_src = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"


        cur.execute('SELECT "Title" FROM "Photos_has_Tags" WHERE "Photo-id" = %s', (photo_id,))
        tags_data = cur.fetchall()
        tags_list_for_ui = [t[0] for t in tags_data]


        comments_list = []

        
        cur.execute('SELECT COUNT(*) FROM "Likes" WHERE "Photo-id" = %s', (photo_id,))
        likes_count = cur.fetchone()[0]

        user_has_liked = False
        if current_user:
            cur.execute('''SELECT 1
                           FROM "Likes"
                           WHERE "Photo-id" = %s
                             AND "User-id" = %s''', (photo_id, current_user))
            if cur.fetchone():
                user_has_liked = True

        photos.append({
            'Photo-id': photo_id,
            'Data': photo_src,
            'Caption': r[2],
            'Tags': tags_list_for_ui,
            'Comments': comments_list,
            'LikesCount': likes_count,
            'UserHasLiked': user_has_liked
        })

    cur.close()
    conn.close()

    return render_template('home.html', photos=photos, active_page='search_tags', current_user=current_user)


@app.route('/add_friend', methods=['POST'])
def add_friend():
    # Προσθέτουμε φίλους από την καρτέλα των μελών της κοινότητας και από τους προτεινόμενους φίλους.
    current_user = session.get('user_id')
    if not current_user:
        return redirect(url_for('login'))

    friend_id = request.form.get('friend_id')

    if str(current_user) == str(friend_id):
        return "Δεν μπορείς να κάνεις φίλο τον εαυτό σου!"

    conn = get_db_connection()
    cur = conn.cursor()
    conn.commit()
    try:
        cur.execute('''
                    INSERT INTO "Users_has_Users" ("User_1", "User_2")
                    VALUES (%s, %s) , (%s,%s)
                        ON CONFLICT DO NOTHING 
                    ''', (current_user, friend_id, friend_id, current_user))
        conn.commit()
    except:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('users'))


@app.route('/my_friends', methods=['GET'])
def my_friends():
    current_user = session.get('user_id')
    if not current_user:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
            SELECT u."User-id", u."Name", u."Surname", u."Data"
            FROM "Users" u
                     JOIN "Users_has_Users" f ON u."User-id" = f."User_2"
            WHERE f."User_1" = %s \
            """
    cur.execute(query, (current_user,))
    rows = cur.fetchall()
    friend_list = []

    for row in rows:
        photo_src = None
        if row[3]:
            img_data = row[3].tobytes() if isinstance(row[3], memoryview) else bytes(row[3])
            photo_src = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"
        friend_list.append({
            'user_id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'photo_src': photo_src
        })
    cur.close()
    conn.close()

    return render_template('users.html', users=friend_list, page_title="My Friends", show_add_button=False)


@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    photo_id = request.form.get('photo_id')
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Διαγράφουμε τη φωτογραφία μόνο αν ανήκει σε άλμπουμ του χρήστη που είναι συνδεδεμένος
        cur.execute('''DELETE
                       FROM "Photos"
                       WHERE "Photo-id" = %s
                         AND "Album-id" IN (SELECT "Album-id"
                                            FROM "Albums"
                                            WHERE "User-id" = %s)''', (photo_id, user_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Σφάλμα Διαγραφής: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(request.referrer or url_for('home', view='mine'))


@app.route('/top_tags', methods=['GET'])
def top_tags():
    conn = get_db_connection()
    cur = conn.cursor()
    # Επιστρέφουμε τις 10 πιο δημοφιλείς ετικέτες, βάσει αριθμού εμφανίσεεών τους σε δημοσιεύσεις
    cur.execute("""SELECT TP."Title", COUNT(*)
                   FROM "Photos_has_Tags" TP
                   GROUP BY TP."Title"
                   ORDER BY COUNT(*) DESC
                   LIMIT 10;""")
    rows = cur.fetchall()
    top_tags = []
    for r in rows:
        top_tags.append({'tag': r[0], 'appearances': r[1]})
    cur.close()
    conn.close()
    return render_template('home.html', tags=top_tags, active_page='tag_leaderboard', current_user=session.get('user_id'))


@app.route('/recommended_friends', methods=['GET'])
def recommended_friend():
    current_user = session.get('user_id')
    if not current_user:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    
    try:
        # Το query τώρα φέρνει και τα στοιχεία του χρήστη από τον πίνακα "Users"
        query = '''
                SELECT p2."User_2", u."Name", u."Surname",u."Data", COUNT(*) AS mutual_count
                FROM "Users_has_Users" p1
                         JOIN "Users_has_Users" p2 ON p1."User_2" = p2."User_1"
                         JOIN "Users" u ON p2."User_2" = u."User-id"
                WHERE p1."User_1" = %s
                  AND p2."User_2" != %s
                  AND p2."User_2" NOT IN (
                            SELECT "User_2" 
                            FROM "Users_has_Users" 
                            WHERE "User_1" = %s)
                GROUP BY p2."User_2", u."Name", u."Surname", u."Data"
                ORDER BY mutual_count DESC;
                '''

        cur.execute(query, (current_user, current_user, current_user))
        results = cur.fetchall()

        recommendations = []
        for r in results:
            photo_src = None
            if r[3]:
                img_data = r[3].tobytes() if isinstance(r[3], memoryview) else bytes(r[3])
                photo_src = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"

            recommendations.append({
                'user_id': r[0],
                'name': r[1],
                'surname': r[2],
                'photo_src': photo_src,
                'mutual_count': r[4]
            })


        return render_template('users.html', users=recommendations, page_title="Προτεινόμενοι Φίλοι",show_add_button=True)

    finally:
        cur.close()
        conn.close()



@app.route('/you_may_also_like', methods=['GET'])
def you_may_also_like():
    current_user = session.get('user_id')
    if not current_user:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Το σύνθετο αυτό query το αναλύουμε στο documentation
        cur.execute('''WITH 
                        TopUserTags AS (
                        SELECT PT."Title"
                        FROM "Photos_has_Tags" PT
                            JOIN "Photos" P ON PT."Photo-id" = P."Photo-id"
                            JOIN "Albums" A ON P."Album-id" = A."Album-id"
                        WHERE A."User-id" = %s
                        GROUP BY PT."Title"
                        ORDER BY COUNT(*) DESC
                        LIMIT 5
                        )
                    SELECT P."Photo-id", P."Data", P."Caption",
                        COUNT(PT."Title") AS matched_tags,
                        (SELECT COUNT(*) FROM "Photos_has_Tags" WHERE "Photo-id" = P."Photo-id") AS total_tags
                    FROM "Photos" P
                    JOIN "Albums" A ON P."Album-id" = A."Album-id"
                    JOIN "Photos_has_Tags" PT ON P."Photo-id" = PT."Photo-id"
                    WHERE A."User-id" != %s
                    AND PT."Title" IN (SELECT "Title" FROM TopUserTags)
                    GROUP BY P."Photo-id", P."Data", P."Caption"
                    ORDER BY matched_tags DESC, total_tags ASC
                    ''', (current_user, current_user))
        
        recommended_photos = cur.fetchall()
        if not recommended_photos:
            return render_template('home.html', photos=[], active_page='you_may_also_like', current_user=current_user, search_query="Ανέβασε φωτογραφίες με ετικέτες για να δεις προτάσεις!")

        photos = []

        for r in recommended_photos:
            photo_id = r[0]
            photo_src = None
            if r[1]:
                img_data = bytes(r[1])
                photo_src = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode('utf-8')}"


            cur.execute('SELECT "Title" FROM "Photos_has_Tags" WHERE "Photo-id" = %s', (photo_id,))
            tags_data = cur.fetchall()
            tags_list_for_ui = [t[0] for t in tags_data]


            comments_list = []

            
            cur.execute('SELECT COUNT(*) FROM "Likes" WHERE "Photo-id" = %s', (photo_id,))
            likes_count = cur.fetchone()[0]

            user_has_liked = False
            if current_user:
                cur.execute('''SELECT 1
                            FROM "Likes"
                            WHERE "Photo-id" = %s
                                AND "User-id" = %s''', (photo_id, current_user))
                if cur.fetchone():
                    user_has_liked = True

            photos.append({
                'Photo-id': photo_id,
                'Data': photo_src,
                'Caption': r[2],
                'Tags': tags_list_for_ui,
                'Comments': comments_list,
                'LikesCount': likes_count,
                'UserHasLiked': user_has_liked
            })

        


        return render_template('home.html', photos=photos, active_page='you_may_also_like', current_user=current_user, search_query="Φωτογραφίες που ίσως σου αρέσουν")

    except Exception as e:
        print(f"Σφάλμα You May Also Like: {e}")
        return redirect(url_for('home'))

    finally:
        cur.close()
        conn.close()


@app.route('/search_comments', methods=['GET'])
def search_comments():
    
    query_text = request.args.get('query_text')

    
    if not query_text or query_text.strip() == '':
        return render_template('search_comments.html')

    conn = get_db_connection()
    cur = conn.cursor()

    # Αναζητούμε σχόλια όπως δίνονται από τον χρήστη και φέρνουμε τους χρήστες που τα έχουν κάνει, 
    # μαζί με το πλήθος των σχολίων που ταιριάζουν σε κάθε χρήστη. Τα αποτελέσματα είναι ταξινομημένα κατά πλήθος ταιριασμάτων σε φθίνουσα σειρά.
    cur.execute('''
                SELECT u."User-id", u."Name", u."Surname", COUNT(*) as match_count
                FROM "Users" u
                         JOIN "Comments" c ON u."User-id" = c."User-id"
                WHERE c."Comment_text" = %s
                GROUP BY u."User-id", u."Name", u."Surname"
                ORDER BY match_count DESC;
                ''', (query_text,))

    rows = cur.fetchall()

    
    users_list = []
    for r in rows:
        users_list.append({
            'user_id': r[0],
            'name': r[1],
            'surname': r[2],
            'match_count': r[3]
        })

    cur.close()
    conn.close()

    
    return render_template('search_comments.html', users=users_list, query_text=query_text)



if __name__ == '__main__':
    app.run(debug=True, port=5001)