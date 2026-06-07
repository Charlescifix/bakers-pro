export type NavItem = {
  label: string;
  href: string;
  icon: string;
  section?: string;
};

export type StatusTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'purple';

export type PageConfig = {
  title: string;
  eyebrow: string;
  description: string;
  primaryAction: string;
  api: string[];
  columns: string[];
  rows: Array<Record<string, string | number>>;
  emptyState: string;
  formFields: string[];
  tabs?: string[];
};

export const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: 'Home' },
  { label: 'Ingredients', href: '/ingredients', icon: 'Box', section: 'Catalogue' },
  { label: 'Packaging', href: '/packaging', icon: 'Package' },
  { label: 'Suppliers', href: '/suppliers', icon: 'Truck' },
  { label: 'Recipes', href: '/recipes', icon: 'BookOpen' },
  { label: 'Products', href: '/products', icon: 'ShoppingBag' },
  { label: 'Customers', href: '/customers', icon: 'Users', section: 'Sales' },
  { label: 'Sales Channels', href: '/sales-channels', icon: 'Store' },
  { label: 'Quotes', href: '/quotes', icon: 'FileText' },
  { label: 'Orders', href: '/orders', icon: 'ClipboardList' },
  { label: 'Production', href: '/production', icon: 'ChefHat', section: 'Production' },
  { label: 'Shopping Lists', href: '/shopping-lists', icon: 'ShoppingCart' },
  { label: 'Imports', href: '/imports', icon: 'Upload', section: 'Data' },
  { label: 'Reports', href: '/reports', icon: 'BarChart2', section: 'Insights' },
  { label: 'Intelligence', href: '/intelligence', icon: 'Zap' },
  { label: 'Allergens & Labels', href: '/allergens', icon: 'Shield', section: 'Compliance' },
  { label: 'Compliance', href: '/compliance', icon: 'ClipboardCheck' },
  { label: 'Settings', href: '/settings', icon: 'Settings', section: 'Account' },
];

export const dashboard = {
  stats: [
    { label: 'Orders Today', value: '12', hint: '+3 vs yesterday', href: '/orders' },
    { label: 'Open Quotes', value: '8', hint: '£1,820 pending', href: '/quotes' },
    { label: 'This Week Revenue', value: '£4,920.00', hint: '+18.4%', href: '/reports' },
    { label: 'This Week Net Profit', value: '£1,748.20', hint: '56.2% margin', href: '/reports' },
  ],
  deliveries: [
    { order: 'BM-O-1042', customer: 'Tara Johnson', date: 'Today, 2:00 PM' },
    { order: 'BM-O-1043', customer: 'Ade Cakes', date: 'Tomorrow, 9:30 AM' },
    { order: 'BM-O-1044', customer: 'Corporate Box', date: 'Fri, 11:00 AM' },
  ],
  lowMargin: [
    { product: 'Mini Banana Bread', margin: 31.2, severity: 'low_margin' },
    { product: 'Meat Pie Party Tray', margin: 38.4, severity: 'high_food_cost' },
  ],
  events: [
    { title: 'Price review recommended', message: 'Butter increased 12.5%; 4 products need review.', severity: 'warning' },
    { title: 'Loss-making quote blocked', message: 'Quote BM-Q-00229 is below target margin.', severity: 'critical' },
  ],
};

export const pageConfigs: Record<string, PageConfig> = {
  ingredients: {
    title: 'Ingredients',
    eyebrow: 'Catalogue',
    description: 'Track purchase prices, waste, stock levels and live base-unit cost for every ingredient.',
    primaryAction: 'Add Ingredient',
    api: ['GET /ingredients', 'POST /ingredients', 'GET /ingredients/low-stock'],
    columns: ['Name', 'Category', 'Default Unit', 'Unit Cost', 'Purchase Price', 'Waste %', 'Supplier'],
    rows: [
      { Name: 'Plain Flour', Category: 'Dry goods', 'Default Unit': 'g', 'Unit Cost': '£0.0018', 'Purchase Price': '£18.20 / 10kg', 'Waste %': '2%', Supplier: 'Booker' },
      { Name: 'Unsalted Butter', Category: 'Dairy', 'Default Unit': 'g', 'Unit Cost': '£0.0088', 'Purchase Price': '£2.20 / 250g', 'Waste %': '1%', Supplier: 'Costco' },
      { Name: 'Nutmeg', Category: 'Spices', 'Default Unit': 'g', 'Unit Cost': '£0.0310', 'Purchase Price': '£3.10 / 100g', 'Waste %': '0%', Supplier: 'Local Market' },
    ],
    emptyState: 'No ingredients yet. Add your first ingredient to start costing recipes.',
    formFields: ['Name', 'Category', 'Default Unit', 'Purchase Price', 'Purchase Quantity', 'Waste %', 'Supplier', 'Reorder Level'],
    tabs: ['All Ingredients', 'Low Stock', 'Price History'],
  },
  packaging: {
    title: 'Packaging',
    eyebrow: 'Catalogue',
    description: 'Manage boxes, labels, wraps and per-item packaging costs.',
    primaryAction: 'Add Packaging',
    api: ['GET /packaging', 'POST /packaging', 'PATCH /packaging/{id}'],
    columns: ['Name', 'Supplier', 'Purchase Price', 'Purchase Qty', 'Unit Cost', 'Stock Qty', 'Reorder Level'],
    rows: [
      { Name: 'Cupcake Box 12', Supplier: 'Cake Stuff', 'Purchase Price': '£32.00', 'Purchase Qty': '100', 'Unit Cost': '£0.3200', 'Stock Qty': '46', 'Reorder Level': '20' },
      { Name: 'Thank You Sticker', Supplier: 'Printful', 'Purchase Price': '£12.00', 'Purchase Qty': '500', 'Unit Cost': '£0.0240', 'Stock Qty': '230', 'Reorder Level': '80' },
    ],
    emptyState: 'No packaging items yet. Add boxes, stickers and wraps to get true costs.',
    formFields: ['Name', 'Supplier', 'Purchase Price', 'Purchase Qty', 'Purchase Unit', 'Current Stock', 'Reorder Level'],
  },
  suppliers: {
    title: 'Suppliers',
    eyebrow: 'Catalogue',
    description: 'Keep ingredient and packaging suppliers in one place.',
    primaryAction: 'Add Supplier',
    api: ['GET /suppliers', 'POST /suppliers'],
    columns: ['Name', 'Type', 'Contact', 'Email', 'Phone', 'Website'],
    rows: [
      { Name: 'Booker', Type: 'ingredient', Contact: 'Trade Desk', Email: 'orders@booker.example', Phone: '020 0000 0000', Website: 'booker.co.uk' },
      { Name: 'Cake Stuff', Type: 'packaging', Contact: 'Sales', Email: 'hello@cakestuff.example', Phone: '0161 000 0000', Website: 'cakestuff.com' },
    ],
    emptyState: 'No suppliers yet. Add your main stockists for better purchasing reports.',
    formFields: ['Name', 'Type', 'Contact Name', 'Email', 'Phone', 'Website', 'Notes'],
  },
  recipes: {
    title: 'Recipes',
    eyebrow: 'Catalogue',
    description: 'Build costed recipes, scale batches and compare version history.',
    primaryAction: 'New Recipe',
    api: ['GET /recipes', 'GET /recipes/{id}/cost-preview', 'POST /recipes/{id}/scale'],
    columns: ['Name', 'Category', 'Base Yield', 'Labour Mins', 'Status', 'Cost Preview'],
    rows: [
      { Name: 'Puff Puff Base', Category: 'Fried', 'Base Yield': '60 pieces', 'Labour Mins': '70', Status: 'active', 'Cost Preview': '£0.19 / item' },
      { Name: 'Meat Pie Filling', Category: 'Pastry', 'Base Yield': '24 pieces', 'Labour Mins': '95', Status: 'draft', 'Cost Preview': '£1.08 / item' },
    ],
    emptyState: 'No recipes yet. Add a base recipe to unlock product pricing.',
    formFields: ['Name', 'Description', 'Base Yield Qty', 'Base Yield Unit', 'Prep Time', 'Bake Time', 'Labour Mins', 'Ingredients', 'Packaging Rules'],
    tabs: ['Ingredients', 'Packaging Rules', 'Versions', 'Cost Preview', 'Scale'],
  },
  products: {
    title: 'Products',
    eyebrow: 'Catalogue',
    description: 'Convert recipes into sellable product variants with live margin summaries.',
    primaryAction: 'Add Product',
    api: ['GET /products', 'POST /products', 'GET /product-variants/{id}/pricing-summary'],
    columns: ['Name', 'Category', '# Variants', 'Default Recipe', 'Margin Status'],
    rows: [
      { Name: 'Puff Puff', Category: 'Party trays', '# Variants': '3', 'Default Recipe': 'Puff Puff Base', 'Margin Status': 'profitable' },
      { Name: 'Meat Pie', Category: 'Pastry', '# Variants': '2', 'Default Recipe': 'Meat Pie Filling', 'Margin Status': 'low_margin' },
    ],
    emptyState: 'No products yet. Add a product and attach variants to begin quoting.',
    formFields: ['Product Name', 'Description', 'Category', 'Image URL', 'Variant Name', 'Recipe', 'Multiplier', 'Selling Price', 'Desired Margin'],
  },
  customers: {
    title: 'Customers',
    eyebrow: 'Sales',
    description: 'Save customer details, social handles and delivery notes.',
    primaryAction: 'Add Customer',
    api: ['GET /customers', 'POST /customers'],
    columns: ['Full Name', 'Company', 'Type', 'Email', 'Phone', 'Instagram'],
    rows: [
      { 'Full Name': 'Tara Johnson', Company: 'Johnson Events', Type: 'corporate', Email: 'tara@example.com', Phone: '07123 000 000', Instagram: '@taraevents' },
      { 'Full Name': 'Amaka Obi', Company: '-', Type: 'individual', Email: 'amaka@example.com', Phone: '07999 000 000', Instagram: '@amakabakes' },
    ],
    emptyState: 'No customers yet. Add your first customer before creating a quote.',
    formFields: ['Full Name', 'Company', 'Email', 'Phone', 'Instagram', 'TikTok', 'Address', 'Postcode', 'Customer Type', 'Notes'],
  },
  'sales-channels': {
    title: 'Sales Channels',
    eyebrow: 'Sales',
    description: 'Model marketplace fees, delivery commissions and payment processing.',
    primaryAction: 'Add Channel',
    api: ['GET /sales-channels', 'POST /sales-channels'],
    columns: ['Name', '% Fee', 'Fixed per Order', 'Fixed per Item', 'Payment %', 'Payment Fixed'],
    rows: [
      { Name: 'Direct WhatsApp', '% Fee': '0%', 'Fixed per Order': '£0.00', 'Fixed per Item': '£0.00', 'Payment %': '1.5%', 'Payment Fixed': '£0.20' },
      { Name: 'Uber Eats', '% Fee': '30%', 'Fixed per Order': '£0.00', 'Fixed per Item': '£0.00', 'Payment %': '0%', 'Payment Fixed': '£0.00' },
    ],
    emptyState: 'No sales channels yet. Add Direct, Instagram or delivery platforms.',
    formFields: ['Name', 'Percentage Fee', 'Fixed Fee per Order', 'Fixed Fee per Item', 'Payment Processing %', 'Payment Fixed', 'Commission Notes'],
  },
  quotes: {
    title: 'Quotes',
    eyebrow: 'Sales',
    description: 'Build profitable quotes, generate WhatsApp messages and convert accepted quotes into orders.',
    primaryAction: 'New Quote',
    api: ['GET /quotes', 'POST /quotes', 'POST /quotes/{id}/generate-message'],
    columns: ['Quote #', 'Customer', 'Status', 'Total Revenue', 'Net Profit', 'Margin %', 'Created'],
    rows: [
      { 'Quote #': 'BM-Q-00231', Customer: 'Tara Johnson', Status: 'draft', 'Total Revenue': '£280.00', 'Net Profit': '£116.40', 'Margin %': '41.6%', Created: 'Today' },
      { 'Quote #': 'BM-Q-00230', Customer: 'Amaka Obi', Status: 'accepted', 'Total Revenue': '£96.00', 'Net Profit': '£51.20', 'Margin %': '53.3%', Created: 'Yesterday' },
    ],
    emptyState: 'No quotes yet. Create a quote or parse a customer message to start.',
    formFields: ['Customer', 'Sales Channel', 'Delivery Method', 'Delivery Date', 'Delivery Fee', 'Desired Margin', 'Discount', 'Line Items'],
  },
  orders: {
    title: 'Orders',
    eyebrow: 'Sales',
    description: 'Track confirmed orders from deposit to delivery and completion.',
    primaryAction: 'New Order',
    api: ['GET /orders', 'PATCH /orders/{id}/status', 'POST /orders/{id}/mark-paid'],
    columns: ['Order #', 'Customer', 'Status', 'Due Date', 'Total', 'Paid', 'Balance'],
    rows: [
      { 'Order #': 'BM-O-1042', Customer: 'Tara Johnson', Status: 'in_production', 'Due Date': 'Today 2:00 PM', Total: '£280.00', Paid: '£140.00', Balance: '£140.00' },
      { 'Order #': 'BM-O-1041', Customer: 'Amaka Obi', Status: 'confirmed', 'Due Date': 'Tomorrow 10:00 AM', Total: '£96.00', Paid: '£96.00', Balance: '£0.00' },
    ],
    emptyState: 'No orders yet. Convert an accepted quote or create one manually.',
    formFields: ['Customer', 'Due Date', 'Status', 'Payment Status', 'Order Items', 'Delivery Notes'],
  },
  production: {
    title: 'Production',
    eyebrow: 'Production',
    description: 'Generate production batches and print checklists for upcoming confirmed orders.',
    primaryAction: 'Generate Plan',
    api: ['POST /production/generate-plan', 'GET /production/batches', 'GET /production/checklist'],
    columns: ['Batch #', 'Recipe', 'Status', 'Planned Yield', 'Planned Start', 'Assigned To'],
    rows: [
      { 'Batch #': 'B-2201', Recipe: 'Puff Puff Base', Status: 'planned', 'Planned Yield': '180 pieces', 'Planned Start': 'Today 9:00 AM', 'Assigned To': 'Chi' },
      { 'Batch #': 'B-2202', Recipe: 'Meat Pie Filling', Status: 'in_progress', 'Planned Yield': '48 pieces', 'Planned Start': 'Today 10:30 AM', 'Assigned To': 'Ade' },
    ],
    emptyState: 'No batches planned. Generate a plan from confirmed orders.',
    formFields: ['Confirmed Orders', 'Assigned Staff', 'Planned Start', 'Notes'],
    tabs: ['Checklist', 'Batches', 'Generate Plan'],
  },
  'shopping-lists': {
    title: 'Shopping Lists',
    eyebrow: 'Production',
    description: 'Calculate what to buy from upcoming orders and group items by supplier.',
    primaryAction: 'Generate List',
    api: ['POST /shopping-lists', 'GET /shopping-lists', 'POST /shopping-lists/{id}/mark-purchased'],
    columns: ['Name', 'Status', 'Total Est. Cost', 'Created', 'Supplier Groups'],
    rows: [
      { Name: 'Weekend Prep', Status: 'draft', 'Total Est. Cost': '£183.40', Created: 'Today', 'Supplier Groups': '4' },
      { Name: 'Corporate Batch', Status: 'purchased', 'Total Est. Cost': '£94.80', Created: 'Yesterday', 'Supplier Groups': '2' },
    ],
    emptyState: 'No shopping lists yet. Generate one from confirmed orders.',
    formFields: ['Name', 'Start Date', 'End Date', 'Orders', 'Group by Supplier'],
  },
  imports: {
    title: 'Imports',
    eyebrow: 'Data',
    description: 'Upload CSV, XLSX or PDF data and review mappings before confirming import.',
    primaryAction: 'Upload File',
    api: ['POST /imports/upload', 'POST /imports/{id}/review-mapping', 'POST /imports/{id}/confirm'],
    columns: ['File', 'Status', 'Confidence', 'Detected Sections', 'Warnings', 'Created'],
    rows: [
      { File: 'costing-template.xlsx', Status: 'needs_review', Confidence: '88%', 'Detected Sections': 'Ingredients, Packaging', Warnings: '2', Created: 'Today' },
      { File: 'old-prices.csv', Status: 'imported', Confidence: '96%', 'Detected Sections': 'Ingredients', Warnings: '0', Created: 'Last week' },
    ],
    emptyState: 'No imports yet. Upload a spreadsheet to speed up setup.',
    formFields: ['File Upload', 'Detected Sections', 'Column Overrides', 'Excluded Sections', 'Confirm Summary'],
    tabs: ['Upload', 'Review Mapping', 'Confirm', 'Result'],
  },
  reports: {
    title: 'Reports',
    eyebrow: 'Insights',
    description: 'Review weekly, monthly, product and channel profitability.',
    primaryAction: 'Export Report',
    api: ['GET /reports/weekly', 'GET /reports/monthly', 'GET /reports/product-profitability'],
    columns: ['Product', 'Variant', 'Selling Price', 'True Cost', 'Gross Profit', 'Net Margin %', 'Status'],
    rows: [
      { Product: 'Puff Puff', Variant: '60 pieces', 'Selling Price': '£45.00', 'True Cost': '£17.10', 'Gross Profit': '£27.90', 'Net Margin %': '62.0%', Status: 'excellent' },
      { Product: 'Meat Pie', Variant: '12 pieces', 'Selling Price': '£34.00', 'True Cost': '£21.40', 'Gross Profit': '£12.60', 'Net Margin %': '37.1%', Status: 'low_margin' },
    ],
    emptyState: 'No report data yet. Complete orders to see profitability reports.',
    formFields: ['Date Range', 'Product Filter', 'Channel Filter', 'Export Format'],
    tabs: ['Weekly', 'Monthly', 'Product Profitability', 'Channel Profitability'],
  },
  intelligence: {
    title: 'Intelligence',
    eyebrow: 'Insights',
    description: 'Parse order messages, ask business questions and generate margin alerts.',
    primaryAction: 'Parse Order Message',
    api: ['POST /intelligence/parse-order-request', 'POST /intelligence/pricing-advice', 'POST /intelligence/ask'],
    columns: ['Event', 'Severity', 'Message', 'Read', 'Created'],
    rows: [
      { Event: 'Margin Alert', Severity: 'warning', Message: 'Meat Pie Party Tray below target margin.', Read: 'No', Created: 'Today' },
      { Event: 'Ask Response', Severity: 'info', Message: 'This week net profit is trending 18% higher.', Read: 'Yes', Created: 'Yesterday' },
    ],
    emptyState: 'No intelligence events yet. Generate margin alerts to begin.',
    formFields: ['Customer Message', 'Detected Items', 'Requested Date', 'Delivery Method', 'Ask Question'],
    tabs: ['Order Parser', 'Pricing Advice', 'Events Feed', 'Ask'],
  },
  allergens: {
    title: 'Allergens & Labels',
    eyebrow: 'Compliance',
    description: 'Maintain allergen matrix and generate printable product labels.',
    primaryAction: 'Generate Label',
    api: ['GET /allergens/matrix', 'POST /labels/generate', 'POST /allergens/seed'],
    columns: ['Product', 'Variant', 'Gluten', 'Milk', 'Eggs', 'Nuts', 'Status'],
    rows: [
      { Product: 'Puff Puff', Variant: 'Classic', Gluten: 'Contains', Milk: 'Free', Eggs: 'Free', Nuts: 'May Contain', Status: 'reviewed' },
      { Product: 'Banana Bread', Variant: 'Mini', Gluten: 'Contains', Milk: 'Contains', Eggs: 'Contains', Nuts: 'Unknown', Status: 'needs_check' },
    ],
    emptyState: 'No allergen matrix yet. Seed UK 14 allergens and tag ingredients.',
    formFields: ['Product Variant', 'Label Type', 'Batch Number', 'Best Before Date', 'Preview HTML'],
    tabs: ['Allergen Matrix', 'Ingredient Allergens', 'Label Generator', 'Seed Allergens'],
  },
  compliance: {
    title: 'Compliance',
    eyebrow: 'Compliance',
    description: 'Record fridge temperatures, cleaning logs and batch compliance notes.',
    primaryAction: 'Add Log',
    api: ['GET /compliance/logs', 'POST /compliance/fridge-temperature', 'POST /compliance/cleaning-log'],
    columns: ['Type', 'Recorded At', 'Recorded By', 'Batch', 'Notes', 'Data'],
    rows: [
      { Type: 'Fridge Temp', 'Recorded At': 'Today 8:00 AM', 'Recorded By': 'Chi', Batch: '-', Notes: 'Normal', Data: '3.4°C' },
      { Type: 'Cleaning', 'Recorded At': 'Yesterday 5:30 PM', 'Recorded By': 'Ade', Batch: '-', Notes: 'Kitchen close', Data: 'Sanitiser A' },
    ],
    emptyState: 'No compliance logs yet. Add a fridge temperature or cleaning record.',
    formFields: ['Log Type', 'Recorded At', 'Related Batch', 'Data', 'Notes'],
    tabs: ['Logs', 'Fridge Temperatures', 'Cleaning Log', 'Batch Records'],
  },
  settings: {
    title: 'Settings',
    eyebrow: 'Account',
    description: 'Manage profile settings and future bakery branding options.',
    primaryAction: 'Save Changes',
    api: ['GET /auth/me'],
    columns: ['Setting', 'Value', 'Status'],
    rows: [
      { Setting: 'Full Name', Value: 'Charles N', Status: 'editable' },
      { Setting: 'Bakery', Value: 'Bold Munch', Status: 'coming soon' },
    ],
    emptyState: 'Settings will appear here after login.',
    formFields: ['Full Name', 'Email', 'Change Password', 'Bakery Name', 'Logo', 'Brand Colours'],
    tabs: ['Profile', 'Bakery'],
  },
};
