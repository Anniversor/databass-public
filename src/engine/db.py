import pandas
import numbers
import os
import sys
try:
    import instabase.notebook.ipython.utils as ib
except:
    pass

openfile = open
try:
    openfile = ib.open
except:
    pass


class Stats(object):

    # XXX: Edit this to compute the table cardinality
    def __init__(self, table):
        self.table = table
        row_size = sys.getsizeof(len(table.rows))
        self.card = int(row_size)

    # XXX: edit this to return the domain of the field
    def __getitem__(self, field):
        type = self.table.type(field)
        d = {}
        distinct = {}
        ndistinct = 0
        if type == "num":
            max = float('inf')
            min = float('inf')
            for row in self.table.rows:
                if row[field] not in distinct:
                    ndistinct += 1
                    distinct[row[field]] = 1
                else:
                    continue
                if row[field] > max:
                    max = row[field]
                elif row[field] < min:
                    min = row[field]
            d["max"] = max
            d["min"] = min
            d["ndistinct"] = ndistinct
        elif type == "str":
            d["max"] = None
            d["min"] = None
            for row in self.table.rows:
                if row[field] not in distinct:
                    ndistinct += 1
                    distinct[row[field]] = 1
            d["ndistinct"] = ndistinct

        return d

class Table(object):
    def __init__(self, fields):
        self.fields = fields

    def type(self, field):
        """
        Instead of maintaining a schema, just check the first row of the table
        """
        for row in self.rows:
            if isinstance(row[field], numbers.Number):
                return "num"
            break
        return "str"

    @staticmethod
    def from_dataframe(df):
        fields = list(df.columns)
        rows = df.T.to_dict().values()
        return InMemoryTable(fields, rows)

    @staticmethod
    def from_rows(rows):
        if not rows:
            return InMemoryTable([], rows)
        return InMemoryTable(rows[0].keys(), rows)

    @property
    def stats(self):
        return Stats(self)

    def col_values(self, field):
        return [row[field] for row in self]

    def __iter__(self):
        yield


class InMemoryTable(Table):
    """
    Table that contains its data all in memory
    """
    def __init__(self, fields, rows):
        super(InMemoryTable, self).__init__(fields)
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)

class Database(object):
    """
    Manages all tables registered in the database
    """
    def __init__(self):
        self.registry = {}
        self.setup()

    def setup(self):
        """
        Walks all CSV files in the current directory and registers
        them in the database
        """
        for root, dirs, files in os.walk("."):
            for fname in files:
                if fname.lower().endswith(".csv"):
                    tablename, _ = os.path.splitext(fname)
                    fpath = os.path.join(root, fname)
                    try:
                        with openfile(fpath) as f:
                            df = pandas.read_csv(f)
                            self.register_dataframe(tablename, df)
                    except Exception as e:
                        print("Failed to read data file %s" % fpath)
                        print(e)

    def register_table(self, tablename, table):
        self.registry[tablename] = table

    def register_dataframe(self, tablename, df):
        self.register_table(tablename, Table.from_dataframe(df))

    @property
    def tablenames(self):
        return self.registry.keys()

    def __contains__(self, tablename):
        return tablename in self.registry

    def __getitem__(self, tablename):
        return self.registry.get(tablename, None)
