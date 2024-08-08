use anyhow::{Result, anyhow};
use chrono::prelude::*;
use pyo3::prelude::*;
use pyo3::types::PyAny;
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
            .ok_or(anyhow!("could not parse PyDate into NaiveDate"))
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
            .ok_or(anyhow!("could not parse PyTime into NaiveTime"))
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
    second: u32
}

impl TryFrom<&PyTimestamp> for NaiveDateTime {
    type Error = anyhow::Error;

    fn try_from(value: &PyTimestamp) -> Result<NaiveDateTime> {
        let naivedate = NaiveDate::from_ymd_opt(value.year, value.month, value.day)
            .ok_or(anyhow!("could not parse a NaiveDate from PyTimestamp"))?;
        let naivetime = NaiveTime::from_hms_opt(value.hour, value.minute, value.second)
            .ok_or(anyhow!("could not parse a NaiveTime from PyTimestamp"))?;
        Ok(naivedate.and_time(naivetime))
    }
}

impl ToSql for PyTimestamp {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let naivedatetime_opt: Result<NaiveDateTime> = self.try_into();
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
    pub fn new(year: i32, month: u32, day: u32, hour: u32, minute: u32, second: u32) -> PyTimestamp {
        PyTimestamp {
            year,
            month,
            day,
            hour,
            minute,
            second,
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
            .ok_or(anyhow!("could not parse PyDateFromTicks into NaiveDate"))?
            .date_naive();
        Ok(naivedate)
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
        let naivedate =  DateTime::from_timestamp(value.ticks, 0)
            .ok_or(anyhow!("could not parse PyTimeFromTicks into NaiveDate"))?
            .time();
        Ok(naivedate)
    }
}

impl ToSql for PyTimeFromTicks {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let naivedate_opt: Result<NaiveTime> = self.try_into();
        match naivedate_opt {
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

impl TryFrom<&PyTimestampFromTicks> for DateTime<Utc> {
    type Error = anyhow::Error;

    fn try_from(value: &PyTimestampFromTicks) -> Result<DateTime<Utc>> {
        let naivedate =  DateTime::from_timestamp(value.ticks, 0)
            .ok_or(anyhow!("could not parse PyTimestampFromTicks into NaiveDate"))?;
        Ok(naivedate)
    }
}

impl ToSql for PyTimestampFromTicks {
    fn to_sql(&self) -> rusqlite::Result<ToSqlOutput<'_>> {
        let naivedate_opt: Result<DateTime<Utc>> = self.try_into();
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
