// Registers
const fastify = require('fastify')({
    logger: true,
    ignoreTrailingSlash: true
});

// require('events').EventEmitter.prototype._maxListeners = 40;
// require('events').defaultMaxListeners = 40;

fastify.register(require('@fastify/postgres'), {
    connectionString: 'postgresql://postgres:1234567890@localhost/fastify'
})

fastify.register(require("@fastify/view"), {
    engine: {
      ejs: require("ejs"),
      templates: '/templates',
    },
});
  
fastify.register(require('@fastify/formbody'))

fastify.register(require('fastify-bcrypt'), {
  saltWorkFactor: 12
})

fastify.register(require('@fastify/cookie'))
fastify.register(require('@fastify/session'), {
  cookieName: 'sessionId',
  secret: '4ec57ae29a0f5ff3a78c932c7b106c3723bf69acce4df5ede8e384d097b81da6',
  cookie: { secure: false },  
});

fastify.addHook('preHandler', (req, reply, next) => {
  if (!req.session.sessionData) {
    req.session.sessionData = { uid: Int8Array, username: String, cart: {}, }
  }
  next()
})


// Routes
fastify.get('/home', (req, reply) => {
    reply.view('templates/home.html')
})

fastify.get('/login', (req, reply) => {
    reply.view('templates/login.ejs')
})

fastify.get('/register', (req, reply) => {
    reply.view('templates/register.html')
})

fastify.get('/items', (req, reply) => {
  if (!req.session.authenticated) {
    reply.redirect('/login')
  }

  fastify.pg.connect(onConnect)
  function onConnect (err, client, release) {
      if (err) return reply.send(err)
      client.query(
        'SELECT * FROM item',
        function onResult (err, result) {
          release()
          if (!err) {
                reply.view('templates/items.ejs',
                {
                  items: result.rows,
                  username: String(req.session.sessionData.username),
                  cust_id: String(req.session.sessionData.uid),
                  cart: req.session.sessionData.cart
                })
              }
          }
      )
  }
})

fastify.post('/login', async (req, reply) => {
  const {username, password} = req.body
  const client = await fastify.pg.connect()
  try {
    const {rows} = await client.query(
      'SELECT * FROM customer WHERE username=$1', [username])
    if (rows) {
      const isCorrect = await fastify.bcrypt.compare(password, rows[0].password);
      if (isCorrect) {
        req.session.authenticated = true
        req.session.sessionData.username = rows[0].username
        req.session.sessionData.uid = rows[0].id
        reply.redirect('/items')
      } else {
        reply.redirect('/login')
      }
    } else {
      reply.redirect('/login')
    }
  } catch(err) {
    reply.redirect('/home')
  } finally {
    client.release()
  }
})

fastify.post('/register', async (req, reply) => {
  const {username, password} = req.body
  let pwd = password
  query = 'INSERT INTO customer (username, password) VALUES($1, $2)'
  const client = await fastify.pg.connect()
  
  try {
    pwd = await fastify.bcrypt.hash(password, 10);
    await client.query(query, [username,  pwd])  
  } catch(err) {
    reply.send(err)
  } finally {
    client.release()
    reply.redirect('/home')
  }
})

/***
 * Method for adding products of cart, in temporary session.
 * Not working with JMeter.
 */
fastify.post('/items/add/:id', (req, reply) => {
  if (!req.session.authenticated) {
    reply.redirect('/login')
  }
  var new_quantity = parseInt(req.body.quantity);
  req.session.sessionData.cart[req.params.id]
    = (req.session.sessionData.cart[req.params.id])
    ? parseInt(req.session.sessionData.cart[req.params.id]) + new_quantity
    : new_quantity;
    
  reply.redirect('/items')
})

/***
 * Method for removing products of cart, from temporary session.
 * Not working with JMeter.
 */
fastify.post('/items/remove/:id', (req, reply) => {
  if (!req.session.authenticated) {
    reply.redirect('/login')
  }
  var new_quantity = parseInt(req.body.quantity)
  if (req.session.sessionData.cart[req.params.id]) {
    var quantity_in_cart = parseInt(req.session.sessionData.cart[req.params.id])
    if (quantity_in_cart >= new_quantity)
      req.session.sessionData.cart[req.params.id] = quantity_in_cart - new_quantity
  }
  reply.redirect('/items')
})

// POST method adds all products in one transaction in database.
fastify.post('/purchase', async (req, reply) => {
  // if (req.session.sessionData.cart == null) reply.redirect('/items')
  const cust_id = req.body.cust_id
  delete req.body.cust_id
  const cart = Object.entries(req.body)
  var query = 'INSERT INTO cart(cart_id, cid, iid, quantity) VALUES ';
  cart.forEach(([key,value]) => {
    if (value != 0) {
      query = query + 
      `, (${cust_id+''+key}, ${cust_id}, ${key}, ${value})`
    }
  })
  query = query.replace('VALUES ,', 'VALUES')
  query = query + ' ON CONFLICT (cart_id) DO UPDATE SET quantity = EXCLUDED.quantity;'  
  const client = await fastify.pg.connect()
  
  try {
    await client.query(query)  
  } catch(err) {
    reply.send(err)
  } finally {
    req.session.sessionData.cart = {}
    client.release()
    reply.redirect('/items')
  }
})

fastify.get('/logout', (req, reply) => {
  if (req.session.authenticated) {
    req.session.destroy(req.session.cookieName)
    reply.redirect('/home')
  }
});

fastify.listen({ port: 5000 }, (err) => {
  if (err) {
    fastify.log.error(err)
    process.exit(1)
  }
})
