CREATE DATABASE IF NOT EXISTS ip_project2022
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ip_project2022;

CREATE TABLE IF NOT EXISTS stocks (
    BatchNo VARCHAR(20) NOT NULL,
    ExpiryDate DATE NOT NULL,
    NameofMedicine VARCHAR(100) NOT NULL,
    Quantity INT NOT NULL DEFAULT 0,
    Price DECIMAL(10, 2) NOT NULL,
    CostPrice DECIMAL(10, 2) NOT NULL DEFAULT 0,
    ManufacturerName VARCHAR(100) NULL,
    ManufacturerPhoneNo VARCHAR(20) NULL,
    MfgDate DATE NULL,
    PRIMARY KEY (BatchNo),
    INDEX idx_stocks_name (NameofMedicine),
    INDEX idx_stocks_expiry (ExpiryDate)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS staffinfo (
    EmpNo VARCHAR(20) NOT NULL,
    Name VARCHAR(100) NOT NULL,
    Gender VARCHAR(30) NULL,
    Age INT NULL,
    Designation VARCHAR(100) NULL,
    Salary DECIMAL(10, 2) NULL,
    AdharNo VARCHAR(20) NOT NULL,
    Doj DATE NULL,
    PRIMARY KEY (EmpNo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customerinformation (
    ID VARCHAR(20) NOT NULL,
    NAME VARCHAR(100) NOT NULL,
    GENDER VARCHAR(30) NOT NULL,
    AGE INT NULL,
    PhoneNumber VARCHAR(20) NULL,
    ReceiptNumber VARCHAR(30) NULL,
    DoctorName VARCHAR(100) NULL,
    Address VARCHAR(255) NULL,
    ReasonForVisit VARCHAR(255) NULL,
    PRIMARY KEY (ID),
    INDEX idx_customer_phone (PhoneNumber)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bills (
    BillID BIGINT NOT NULL AUTO_INCREMENT,
    ReceiptNumber VARCHAR(40) NOT NULL,
    DATEOFBILL DATETIME NOT NULL,
    CustomerID VARCHAR(20) NULL,
    CustomerName VARCHAR(100) NULL,
    CustomerPhone VARCHAR(20) NULL,
    Subtotal DECIMAL(12, 2) NOT NULL,
    GSTRate DECIMAL(5, 2) NOT NULL,
    GSTAmount DECIMAL(12, 2) NOT NULL,
    Total DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (BillID),
    UNIQUE KEY uq_bills_receipt (ReceiptNumber),
    INDEX idx_bills_date (DATEOFBILL),
    CONSTRAINT fk_bills_customer
        FOREIGN KEY (CustomerID) REFERENCES customerinformation (ID)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bill_items (
    BillItemID BIGINT NOT NULL AUTO_INCREMENT,
    BillID BIGINT NOT NULL,
    BatchNo VARCHAR(20) NOT NULL,
    MedicineName VARCHAR(100) NOT NULL,
    BillQuantity INT NOT NULL,
    UnitPrice DECIMAL(10, 2) NOT NULL,
    UnitCost DECIMAL(10, 2) NOT NULL,
    LineTotal DECIMAL(12, 2) NOT NULL,
    PRIMARY KEY (BillItemID),
    UNIQUE KEY uq_bill_batch (BillID, BatchNo),
    INDEX idx_bill_items_batch (BatchNo),
    CONSTRAINT fk_bill_items_bill
        FOREIGN KEY (BillID) REFERENCES bills (BillID)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_bill_items_stock
        FOREIGN KEY (BatchNo) REFERENCES stocks (BatchNo)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS expenses (
    ExpenseID BIGINT NOT NULL AUTO_INCREMENT,
    ExpenseDate DATE NOT NULL,
    Category VARCHAR(100) NOT NULL,
    Amount DECIMAL(12, 2) NOT NULL,
    Description VARCHAR(255) NULL,
    PRIMARY KEY (ExpenseID),
    INDEX idx_expenses_date (ExpenseDate)
) ENGINE=InnoDB;
