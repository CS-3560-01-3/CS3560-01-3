
/*
Foreign key order matters

Tables must be created in this order:

buyer
category
supplier
item
order
order_item
payment

relational system:

buyer → users
item → products
category → grouping
supplier → source
order → purchases
order_item → connects items to orders
payment → billing
*/

USE basic_business_backend;

START TRANSACTION;

INSERT INTO category (categoryName) VALUES
('Clothing'),
('Books');

INSERT INTO supplier (email, address) VALUES
('sup2@test.com', 'LA'),
('sup3@test.com', 'Chicago');

INSERT INTO item (itemName, supplierID, stock, threshold, categoryID)
VALUES
('Graphic T-Shirt', 2, 75, 15, 2),
('Hoodie', 2, 35, 8, 2),
('Notebook Journal', 3, 90, 25, 3);

COMMIT;
