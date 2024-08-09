use anyhow::{Result, anyhow};
use chrono_tz::Tz;
use chrono::prelude::*;
use pyo3::prelude::*;
use pyo3::exceptions::{PyException, PyValueError};
use pyo3::intern;
use pyo3::types::{PyBytes, PyDateTime, PyDateAccess, PyTimeAccess, PyTzInfoAccess};
use rusqlite::types::{ToSql, ToSqlOutput, Value, ValueRef};

const DATE_FORMAT: &str = "%Y-%m-%d";
const TIME_FORMAT: &str = "%H:%M:%S";
const DATETIME_FORMAT: &str = "%Y-%m-%d %H:%M:%S";

#[pyclass(get_all, set_all, module="types", name="Date")]
pub struct PyDate {
    year: i32,
    month: u32,
    day: u32,
}

impl TryFrom<&PyDate> for NaiveDate {
    type Error = anyhow::Error;

    fn try_from(value: &PyDate) -> Result<NaiveDate> {
        NaiveDate::from_ymd_opt(value.year, value.month, value.day)
            .ok_or_else(|| anyhow!("could not parse PyDate into NaiveDate"))
    }
}

impl From<Bound<'_, pyo3::types::PyDate>> for PyDate {
    fn from(value: Bound<'_, pyo3::types::PyDate>) -> Self {
        PyDate {
            year: value.get_year(),
            month: value.get_month() as u32,
            day: value.get_day() as u32,
        }
    }
}

impl ToSql for PyDate {
    fn to_sql(&self) -> rusqlite::Result<rusqlite::types::ToSqlOutput<'_>> {
        let naivedate_opt: Result<NaiveDate> = self.try_into();
        match naivedate_opt {
            Ok(naivedate) => Ok(ToSqlOutput::Owned(Value::Text(naivedate.format(DATE_FORMAT).to_string()))),
            Err(err) => Err(rusqlite::Error::ToSqlConversionFailure(err.into()))
        }
    }
}

#[pymethods]
impl PyDate {
    #[new]
    pub fn new(year: i32, month: u32, day: u32) -> PyDate {
        PyDate {
            year,
            month,
            day,
        }
    }
}

#[pyclass(get_all, set_all, module="types", name="Time")]
pub struct PyTime {
    hour: u32,
    minute: u32,
    second: u32,
}

impl TryFrom<&PyTime> for NaiveTime {
    type Error = anyhow::Error;

    fn try_from(value: &PyTime) -> Result<NaiveTime> {
        NaiveTime::from_hms_opt(value.hour, value.minute, value.second)
            .ok_or_else(|| anyhow!("could not parse PyTime into NaiveTime"))
    }
}

impl From<Bound<'_, pyo3::types::PyTime>> for PyTime {
    fn from(value: Bound<'_, pyo3::types::PyTime>) -> Self {
        PyTime {
            hour: value.get_hour() as u32,
            minute: value.get_minute() as u32,
            second: value.get_second() as u32,
        }
    }
}

impl ToSql for PyTime {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let nativetime_opt: Result<NaiveTime> = self.try_into();
        match nativetime_opt {
            Ok(naivetime) => Ok(ToSqlOutput::Owned(Value::Text(naivetime.format(TIME_FORMAT).to_string()))),
            Err(err) => Err(rusqlite::Error::ToSqlConversionFailure(err.into())),
        }
    }
}

#[pymethods]
impl PyTime{
    #[new]
    pub fn new(hour: u32, minute: u32, second: u32) -> PyTime {
        PyTime {
            hour,
            minute,
            second,
        }
    }
}

#[pyclass(get_all, set_all, module="types", name="Timestamp")]
pub struct PyTimestamp {
    year: i32,
    month: u32,
    day: u32,
    hour: u32,
    minute: u32,
    second: u32,
    tzinfo: Tz,
}

impl TryFrom<&PyTimestamp> for DateTime<Tz> {
    type Error = anyhow::Error;

    fn try_from(value: &PyTimestamp) -> Result<DateTime<Tz>> {
        let naivedate = NaiveDate::from_ymd_opt(value.year, value.month, value.day)
            .ok_or_else(|| anyhow!("could not parse a NaiveDate from PyTimestamp"))?;
        let naivetime = NaiveTime::from_hms_opt(value.hour, value.minute, value.second)
            .ok_or_else(|| anyhow!("could not parse a NaiveTime from PyTimestamp"))?;
        let fq_datetime = naivedate.and_time(naivetime).and_local_timezone(value.tzinfo);
        // TODO: Better logic for choosing ambiguous time
        match fq_datetime {
            chrono::offset::LocalResult::Single(datetime) => Ok(datetime.with_timezone(&Tz::UTC)),
            chrono::offset::LocalResult::Ambiguous(early, _) => Ok(early.with_timezone(&Tz::UTC)),
            chrono::offset::LocalResult::None => Err(anyhow!("could not assign correct timezone (is the time a gap from daylight savings?)")),
        }
    }
}

impl From<Bound<'_, PyDateTime>> for PyTimestamp {
    fn from(value: Bound<'_, PyDateTime>) -> Self {
        let tzinfo: Tz = if let Some(pytzinfo) = value.get_tzinfo_bound() {
            pytzinfo.extract().unwrap_or(Tz::UTC)
        } else {
            // TODO: Assume UTC if we can't get tz from Python, is that ok?
            Tz::UTC
        };
        PyTimestamp {
            year: value.get_year(),
            month: value.get_month() as u32,
            day: value.get_day() as u32,
            hour: value.get_hour() as u32,
            minute: value.get_minute() as u32,
            second: value.get_second() as u32,
            tzinfo,
        }
    }
}

impl ToSql for PyTimestamp {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let naivedatetime_opt: Result<DateTime<Tz>> = self.try_into();
        match naivedatetime_opt {
            Ok(naivedatetime) => Ok(
                ToSqlOutput::Owned(Value::Text(naivedatetime.format(DATETIME_FORMAT).to_string()))
            ),
            Err(err) => Err(rusqlite::Error::ToSqlConversionFailure(err.into()))
        }
    }
}

#[pymethods]
impl PyTimestamp {
    #[new]
    pub fn new(year: i32, month: u32, day: u32, hour: u32, minute: u32, second: u32, tzinfo: Tz) -> PyTimestamp {
        PyTimestamp {
            year,
            month,
            day,
            hour,
            minute,
            second,
            tzinfo,
        }
    }
}

#[pyclass(module="types", name="DateFromTicks")]
pub struct PyDateFromTicks {
    #[pyo3(get, set)]
    ticks: i64,
}

impl TryFrom<&PyDateFromTicks> for NaiveDate {
    type Error = anyhow::Error;

    fn try_from(value: &PyDateFromTicks) -> Result<NaiveDate> {
        let naivedate =  DateTime::from_timestamp(value.ticks, 0)
            .ok_or_else(|| anyhow!("could not parse PyDateFromTicks into NaiveDate"))?
            .date_naive();
        Ok(naivedate)
    }
}

impl TryFrom<Bound<'_, pyo3::types::PyDate>> for PyDateFromTicks {
    type Error = PyErr;

    fn try_from(value: Bound<'_, pyo3::types::PyDate>) -> PyResult<PyDateFromTicks> {
        let ticks: i64 = value.call_method0(intern!(value.py(), "timestamp"))?.extract()?;
        Ok(PyDateFromTicks { ticks })
    }
}

impl ToSql for PyDateFromTicks {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let naivedate_opt: Result<NaiveDate> = self.try_into();
        match naivedate_opt {
            Ok(naivedate) => Ok(ToSqlOutput::Owned(Value::Text(naivedate.format(DATE_FORMAT).to_string()))),
            Err(err) => Err(rusqlite::Error::ToSqlConversionFailure(err.into()))
        }
    }
}

#[pymethods]
impl PyDateFromTicks {
    #[new]
    pub fn new(ticks: i64) -> PyDateFromTicks {
        PyDateFromTicks { ticks }
    }
}

#[pyclass(module="types", name="TimeFromTicks")]
pub struct PyTimeFromTicks {
    #[pyo3(get, set)]
    ticks: i64,
}

impl TryFrom<&PyTimeFromTicks> for NaiveTime {
    type Error = anyhow::Error;

    fn try_from(value: &PyTimeFromTicks) -> Result<NaiveTime> {
        Ok(
            DateTime::from_timestamp(value.ticks, 0)
                .ok_or_else(|| anyhow!("could not parse ticks into valid date"))?
                .time()
        )
    }
}

impl TryFrom<Bound<'_, pyo3::types::PyTime>> for PyTimeFromTicks {
    type Error = PyErr;

    fn try_from(value: Bound<'_, pyo3::types::PyTime>) -> PyResult<PyTimeFromTicks> {
        let ticks: i64 = value.call_method0(intern!(value.py(), "timestamp"))?.extract()?;
        Ok(PyTimeFromTicks { ticks })
    }
}

impl ToSql for PyTimeFromTicks {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let naivetime_opt: Result<NaiveTime> = self.try_into();
        match naivetime_opt {
            Ok(naivetime) => Ok(ToSqlOutput::Owned(Value::Text(naivetime.format(TIME_FORMAT).to_string()))),
            Err(err) => Err(rusqlite::Error::ToSqlConversionFailure(err.into()))
        }
    }
}

#[pymethods]
impl PyTimeFromTicks {
    #[new]
    pub fn new(ticks: i64) -> PyTimeFromTicks {
        PyTimeFromTicks { ticks }
    }
}

#[pyclass(module="types", name="TimestampFromTicks")]
pub struct PyTimestampFromTicks {
    #[pyo3(get, set)]
    ticks: i64,
}

impl TryFrom<&PyTimestampFromTicks> for DateTime<Tz> {
    type Error = anyhow::Error;

    fn try_from(value: &PyTimestampFromTicks) -> Result<DateTime<Tz>> {
        let naivedate =  DateTime::from_timestamp(value.ticks, 0)
            .ok_or_else(|| anyhow!("could not parse PyTimestampFromTicks into NaiveDate"))?
            .with_timezone(&Tz::UTC);
        Ok(naivedate)
    }
}

impl TryFrom<Bound<'_, pyo3::types::PyDateTime>> for PyTimestampFromTicks {
    type Error = PyErr;

    fn try_from(value: Bound<'_, pyo3::types::PyDateTime>) -> PyResult<PyTimestampFromTicks> {
        let ticks: i64 = value.call_method0(intern!(value.py(), "timestamp"))?.extract()?;
        Ok(PyTimestampFromTicks { ticks })
    }
}

impl ToSql for PyTimestampFromTicks {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let naivedate_opt: Result<DateTime<Tz>> = self.try_into();
        match naivedate_opt {
            Ok(naivetime) => Ok(ToSqlOutput::Owned(Value::Text(naivetime.format(TIME_FORMAT).to_string()))),
            Err(err) => Err(rusqlite::Error::ToSqlConversionFailure(err.into()))
        }
    }
}

#[pymethods]
impl PyTimestampFromTicks {
    #[new]
    pub fn new(ticks: i64) -> PyTimestampFromTicks {
        PyTimestampFromTicks { ticks }
    }
}

#[pyclass(module="types", name="Binary")]
pub struct PyBinary {
    #[pyo3(get, set)]
    value: Vec<u8>,
}

impl TryFrom<Bound<'_, PyBytes>> for PyBinary {
    type Error = PyErr;

    fn try_from(value: Bound<'_, PyBytes>) -> PyResult<PyBinary> {
        let data: Vec<u8> = value.extract()?;
        Ok(PyBinary { value: data })
    }
}

impl ToSql for PyBinary {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        Ok(ToSqlOutput::Borrowed(ValueRef::Blob(self.value.as_slice())))
    }
}

#[pyclass(frozen, module="types", name="STRING")]
pub struct PySqliteString;

#[pyclass(frozen, module="types", name="BINARY")]
pub struct PySqliteBinary;

#[pyclass(frozen, module="types", name="NUMBER")]
pub struct PySqliteNumber;

#[pyclass(frozen, module="types", name="DATETIME")]
pub struct PySqliteDateTime;

#[pyclass(frozen, module="types", name="ROWID")]
pub struct PySqliteRowId;
