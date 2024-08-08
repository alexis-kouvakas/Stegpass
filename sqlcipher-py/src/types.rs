use anyhow::{Result, anyhow};
use chrono::prelude::*;
use pyo3::prelude::*;
use rusqlite::types::{ToSql, ToSqlOutput, Value};

const DATE_FORMAT: &str = "%Y-%m-%d";
const TIME_FORMAT: &str = "%H:%M:%S";
const DATETIME_FORMAT: &str = "%Y-%m-%d %H:%M:%S";

#[pyclass(get_all, set_all, module="types", name="Date")]
struct PyDate {
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
    fn new(year: i32, month: u32, day: u32) -> PyDate {
        PyDate {
            year,
            month,
            day,
        }
    }
}

#[pyclass(get_all, set_all, module="types", name="Time")]
struct PyTime {
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
    fn new(hour: u32, minute: u32, second: u32) -> PyTime {
        PyTime {
            hour,
            minute,
            second,
        }
    }
}

#[pyclass(get_all, set_all, module="types", name="Timestamp")]
struct PyTimestamp {
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

#[pyclass(module="types", name="DateFromTicks")]
struct PyDateFromTicks {
    #[pyo3(get, set)]
    ticks: i64,
}
