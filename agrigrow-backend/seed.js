// seed.js — Seed demo accounts and sample data
require('dotenv').config();
const bcrypt = require('bcryptjs');
const { dbRun, dbGet, dbAll, initDb, initBadgesForUser, initTasksForUser } = require('./db/database');

const today = new Date().toISOString().split('T')[0];

async function seed() {
  await initDb();
  console.log('\n🌱 Seeding AgriGrow database...\n');

  // Demo Farmer
  let farmerId;
  const existingFarmer = await dbGet("SELECT id FROM users WHERE email = 'farmer@demo.com'");
  if (!existingFarmer) {
    const hash = await bcrypt.hash('farm123', 10);
    const res = await dbRun(
      `INSERT INTO users (name, email, password, role, region, crop_type, farm_size, experience, points, streak)
       VALUES ('Demo Farmer', 'farmer@demo.com', ?, 'farmer', 'Tamil Nadu', 'Rice', '5', '3-5 years', 120, 3)`,
      [hash]
    );
    farmerId = res.lastID;
    await initBadgesForUser(farmerId);
    await initTasksForUser(farmerId, today);
    await dbRun("INSERT OR IGNORE INTO completed_lessons (user_id, lesson_id, pts) VALUES (?, '1a', 30)", [farmerId]);
    await dbRun("UPDATE badges SET earned = 1 WHERE user_id = ? AND badge_id = 'b1'", [farmerId]);
    console.log('✅ Demo Farmer created  → farmer@demo.com / farm123');
  } else {
    farmerId = existingFarmer.id;
    console.log('⏭️  Demo Farmer already exists');
  }

  // Admin
  const existingAdmin = await dbGet("SELECT id FROM users WHERE email = 'admin@agrigrow.app'");
  if (!existingAdmin) {
    const hash = await bcrypt.hash('admin123', 10);
    await dbRun(
      `INSERT INTO users (name, email, password, role, region, points) VALUES ('Admin', 'admin@agrigrow.app', ?, 'admin', 'Chennai', 0)`,
      [hash]
    );
    console.log('✅ Admin created        → admin@agrigrow.app / admin123');
  } else {
    console.log('⏭️  Admin already exists');
  }

  // Expert users
  const experts = [
    { name: 'Dr. Meera Nair',  email: 'meera@agrigrow.app',  region: 'Chennai'    },
    { name: 'Dr. Ramesh Iyer', email: 'ramesh@agrigrow.app', region: 'Bangalore'  },
  ];
  const expertIds = {};
  for (const exp of experts) {
    const existing = await dbGet('SELECT id FROM users WHERE email = ?', [exp.email]);
    if (!existing) {
      const hash = await bcrypt.hash('expert123', 10);
      const res = await dbRun(
        `INSERT INTO users (name, email, password, role, region, points) VALUES (?, ?, ?, 'expert', ?, 500)`,
        [exp.name, exp.email, hash, exp.region]
      );
      expertIds[exp.name] = res.lastID;
      await initBadgesForUser(res.lastID);
    } else {
      expertIds[exp.name] = existing.id;
    }
  }
  console.log('✅ Expert users ready');

  // Leaderboard users
  const lbUsers = [
    { name: 'Ramesh Kumar', region: 'Tamil Nadu',     pts: 1240 },
    { name: 'Priya Devi',   region: 'Karnataka',      pts: 1080 },
    { name: 'Muthu Selvam', region: 'Tamil Nadu',     pts: 960  },
    { name: 'Kavitha R.',   region: 'Andhra Pradesh', pts: 880  },
    { name: 'Srinivas B.',  region: 'Telangana',      pts: 790  },
  ];
  for (const u of lbUsers) {
    const existing = await dbGet('SELECT id FROM users WHERE name = ?', [u.name]);
    if (!existing) {
      const hash = await bcrypt.hash('demo123', 10);
      const res = await dbRun(
        `INSERT INTO users (name, email, password, role, region, crop_type, points, streak) VALUES (?, ?, ?, 'farmer', ?, 'Rice', ?, 5)`,
        [u.name, u.name.toLowerCase().replace(/\s|\./g, '') + '@demo.com', hash, u.region, u.pts]
      );
      await initBadgesForUser(res.lastID);
    }
  }
  console.log('✅ Leaderboard users seeded');

  // Sample forum posts
  const postCount = await dbGet('SELECT COUNT(*) as cnt FROM posts');
  if (postCount.cnt === 0) {
    const meeraId  = expertIds['Dr. Meera Nair']  || farmerId;
    const posts = [
      [meeraId, 'Dr. Meera Nair', 1, 'Soil', 'Verified tip: Adding biochar to sandy soils can improve water retention by up to 40%. Mix 1kg per 10m² for best results.', 24, 'Dr. Meera Nair', 'Always pair biochar with compost — biochar alone can temporarily reduce available nitrogen.', 1],
      [farmerId, 'Sundar Rajan', 0, 'Water', 'Switched to drip irrigation last month and my water bill dropped significantly. Anyone noticed reduced pest pressure too?', 11, null, null, 0],
      [farmerId, 'Anitha Krishnan', 0, 'Pests', 'My tomatoes are attacked by whiteflies. I tried neem oil spray but the infestation returned after 3 days. Should I increase frequency?', 5, 'Dr. Ramesh Iyer', 'Spray every 3 days for the first 2 weeks, then reduce to weekly. Also place yellow sticky traps near plants.', 1],
      [farmerId, 'Vijay Kumar', 0, 'Rotation', 'Started my first crop rotation this season — replaced paddy with cowpea. The soil looks healthier already!', 18, null, null, 0],
    ];
    for (const p of posts) {
      await dbRun(
        'INSERT INTO posts (user_id, author, is_expert, tag, body, likes, reply_author, reply_text, reply_is_expert) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        p
      );
    }
    console.log('✅ Sample forum posts created');
  } else {
    console.log('⏭️  Forum posts already exist');
  }

  console.log('\n🎉 Done! Start the server with:  cd agrigrow-backend && npm run dev\n');
  process.exit(0);
}

seed().catch(err => { console.error('❌ Seed failed:', err); process.exit(1); });
