# Create db model

from app import db 

class Queries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False, index=True)
    query_text = db.Column(db.String(200), nullable=False, index=True)

    # Create a function to return a string when we add something
    def __repr__(self):
        return '<Query {}>'.format(self.id)

# Test utility methods
def insert_query(id, category, query_text):
    q = Queries(id=id, category=category, query_text=query_text)
    db.session.add(q)
    db.session.commit()

def remove_query(id):
    q = Queries.query.get(int(id))
    db.session.delete(q)
    db.session.commit()

def get_query_by_id(id):
    return Queries.query.get(int(id))

def update_category(id, category):
    q = Queries.get_query_by_id(id)
    q.category = category
    db.session.commit()

def update_query_text(id, query_text):
    q = Queries.get_query_by_id(id)
    q.query_text = query_text
    db.session.commit()

def remove_all_queries():
    queries = Queries.query.all()
    for q in queries:
        db.session.delete(q)
    db.session.commit()

def get_all_query_text():
    """ Returns a list of all answerable questions. """
    all_query_text = []
    queries = Queries.query.all()
    for q in queries:
        all_query_text.append(q.query_text)
    return all_query_text