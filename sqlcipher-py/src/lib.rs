mod types;
use delegate::delegate;
use pyo3::prelude::*;
use pyo3::create_exception;
use pyo3::exceptions::PyException;
use rusqlite::{Connection, ToSql};
use rusqlite::Error::SqliteFailure;
use std::cell::RefCell;
use std::path::PathBuf;
use std::rc::{Rc, Weak};

create_exception!(sqlcipher, Warning, PyException);
create_exception!(sqlcipher, Error, PyException);
create_exception!(sqlcipher, InterfaceError, Error);
create_exception!(sqlcipher, DatabaseError, Error);
create_exception!(sqlcipher, DataError, DatabaseError);
create_exception!(sqlcipher, OperationalError, DatabaseError);
create_exception!(sqlcipher, IntegrityError, DatabaseError);
create_exception!(sqlcipher, ProgrammingError, DatabaseError);
create_exception!(sqlcipher, NotSupportedError, DatabaseError);

struct PyConnectionCore {
    connection: Connection,
}

impl PyConnectionCore {
    fn new(connection: Connection) -> PyConnectionCore {
        // TODO: Check if connection is good before returning struct
        PyConnectionCore { connection }
    }

    delegate! {
        to self.connection {
            pub fn execute<P: rusqlite::Params>(&self, sql: &str, params: P) -> rusqlite::Result<usize>;
            pub fn prepare(&self, sql: &str) -> rusqlite::Result<rusqlite::Statement<'_>>;
            pub fn close(self);
        }
    }
}

/// Connection to an SQLite database.
///
/// Note: rusqlite::Connection does implement Send, but
/// currently can't figure out how to store Connection safely.
#[pyclass(unsendable, module="sqlcipher", name="Connection")]
struct PyConnection(Rc<RefCell<PyConnectionCore>>);

impl PyConnection {
    fn new(pyconn_ref: Rc<RefCell<PyConnectionCore>>) -> PyConnection {
        PyConnection(pyconn_ref)
    }
}

#[pymethods]
impl PyConnection {
    fn close(&self) -> PyResult<()> {
        todo!()
    }

    fn commit(&self) -> PyResult<()> {
        todo!()
    }

    fn rollback(&self) -> PyResult<bool> {
        todo!()
    }

    #[pyo3(signature = (as_dict=false))]
    fn cursor(&self, as_dict: bool) -> PyResult<PyCursor> {
        Ok(PyCursor::new(Rc::downgrade(&self.0), as_dict))
    }

    #[pyo3(signature = (query, params_opt=None))]
    fn execute(&self, query: &str, params_opt: Option<Bound<'_, PyAny>>) -> PyResult<i32> {
        let inner = self.0.try_borrow().map_err(|_| PyException::new_err("could not access connection object"))?;
        let statement = inner.prepare(query).map_err(|_| PyException::new_err("could not prepare query"))?;
        if let Some(params) = params_opt {
            todo!()
        }
        /*
        let statement = inner.
            match err {
                SqliteFailure(err, msg_opt) => {
                    let code = err.extended_code;
                    if let Some(msg) = msg_opt {
                        DatabaseError::new_err(format!("encountered error code {code} while preparing query: {msg}"))
                    } else {
                        DatabaseError::new_err(format!("encountered error code {code} while preparing query"))
                    }
                },
                _ => Error::new_err("could not prepare query")
            }
        })?;
        */
        Ok(0)
    }
}

fn process_python_params(params: Bound<'_, PyAny>) -> PyResult<Vec<Box<dyn ToSql>>> {
    todo!()
}

#[pyclass(unsendable, module="sqlcipher", name="Cursor")]
struct PyCursor {
    #[pyo3(get)]
    description: Option<(Option<String>, String, Option<String>, Option<String>, Option<String>, Option<String>, Option<String>)>,
    #[pyo3(get)]
    rowcount: u32,
    closed: bool,
    as_dict: bool,
    connection: Weak<RefCell<PyConnectionCore>>,  // rusqlite::Connection does not implement Sync (https://github.com/rusqlite/rusqlite/issues/188),
}

impl PyCursor {
    fn new(connection: Weak<RefCell<PyConnectionCore>>, as_dict: bool) -> Self {
        PyCursor {
            description: None,
            rowcount: 0,
            closed: false,
            as_dict,
            connection,
        }
    }
}

#[pymethods]
impl PyCursor {
    fn close(&mut self) {
        self.closed = true;
    }
}

fn as_pathbuf<'py>(obj: &Bound<'py, PyAny>) -> PyResult<PathBuf> {
    Ok(obj.str()?.extract()?)
}

/// Connect to an SQLCipher/SQLite database file.
#[pyfunction]
fn connect(#[pyo3(from_py_with = "as_pathbuf")] filename: PathBuf) -> PyResult<PyConnection> {
    match Connection::open(&filename) {
        Ok(conn) => Ok(PyConnection::new(Rc::new(RefCell::new(PyConnectionCore::new(conn))))),
        Err(e) => match e {
            SqliteFailure(err, msg_opt) => {
                let code = err.extended_code;
                if let Some(msg) = msg_opt {
                    let error_msg = format!("encountered error code {code} while connecting: {msg}");
                    Err(DatabaseError::new_err(error_msg))
                } else {
                    Err(DatabaseError::new_err(format!("encountered error code {code} while connecting")))
                }
            },
            _ => Err(Error::new_err("could not connect to database"))
        },
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn sqlcipher(m: &Bound<'_, PyModule>) -> PyResult<()> {
    use crate::types::*;
    m.add("apilevel", "2.0")?;
    m.add("threadsafety", 0)?;
    m.add("paramstyle", "qmark")?;
    m.add("Warning", m.py().get_type_bound::<Warning>())?;
    m.add("Error", m.py().get_type_bound::<Error>())?;
    m.add("InterfaceError", m.py().get_type_bound::<InterfaceError>())?;
    m.add("DatabaseError", m.py().get_type_bound::<DatabaseError>())?;
    m.add("DataError", m.py().get_type_bound::<DataError>())?;
    m.add("OperationalError", m.py().get_type_bound::<OperationalError>())?;
    m.add("IntegrityError", m.py().get_type_bound::<IntegrityError>())?;
    m.add("ProgrammingError", m.py().get_type_bound::<ProgrammingError>())?;
    m.add("NotSupportedError", m.py().get_type_bound::<NotSupportedError>())?;
    m.add_class::<PyDate>()?;
    m.add_class::<PyTime>()?;
    m.add_class::<PyTimestamp>()?;
    m.add_class::<PyDateFromTicks>()?;
    m.add_class::<PyTimeFromTicks>()?;
    m.add_class::<PyTimestampFromTicks>()?;
    m.add_class::<PyBinary>()?;
    m.add_class::<PySqliteString>()?;
    m.add_class::<PySqliteBinary>()?;
    m.add_class::<PySqliteNumber>()?;
    m.add_class::<PySqliteDateTime>()?;
    m.add_class::<PySqliteRowId>()?;
    m.add_class::<PyConnection>()?;
    m.add_class::<PyCursor>()?;
    m.add_function(wrap_pyfunction!(connect, m)?)?;
    Ok(())
}
