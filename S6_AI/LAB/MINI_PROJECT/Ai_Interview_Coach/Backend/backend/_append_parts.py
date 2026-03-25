"""Script to append Part 2 (Mistral AI) and Part 3 (API endpoints) to app.py"""
import os

PART2 = r'''

# ==============================================================================
#  MISTRAL AI AGENT - ENTERPRISE GRADE
# ==============================================================================

COMPANY_STYLES = {
    'google':    "Google favours deep algorithmic thinking, system design at scale, and STAR behavioral answers.",
    'amazon':    "Amazon uses Leadership Principles for behaviorals. Expect coding, system design, and LP stories.",
    'microsoft': "Microsoft balances coding fundamentals, design, and growth-mindset culture fit.",
    'meta':      "Meta focuses on speed + correctness in coding, product sense, and collaboration at massive scale.",
    'apple':     "Apple values quality, detail, and product thinking. Deep dives into past projects.",
    'netflix':   "Netflix values high performance, independent decision-making, and data-driven thinking.",
    'startup':   "Startups value versatility, speed, and ownership. Broad scope and product intuition.",
    'default':   "Focus on solid fundamentals, clear communication, and real-world problem-solving.",
}

DIFFICULTY_MAP = {
    'entry':   ('easy',   'warm-up and intermediate level'),
    'junior':  ('easy',   'warm-up and intermediate level'),
    'mid':     ('medium', 'intermediate and advanced level'),
    'senior':  ('hard',   'advanced and expert level'),
    'lead':    ('expert', 'expert and architecture-level'),
    'default': ('medium', 'intermediate level'),
}


class MistralAIAgent:
    """Enterprise Mistral AI - company-aware question generation + 6-dimension scoring."""

    def __init__(self):
        self.base_url   = os.environ.get('MISTRAL_BASE_URL',   'http://127.0.0.1:1234/v1')
        self.model_name = os.environ.get('MISTRAL_MODEL_NAME', 'mistral-7b-instruct-v0.2')
        api_key         = os.environ.get('MISTRAL_API_KEY',    'lm-studio')
        self.is_available = False
        print(f"\n Connecting to Mistral AI at: {self.base_url}")
        print(f" Model: {self.model_name}")
        try:
            self.client = OpenAI(base_url=self.base_url, api_key=api_key)
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5)
            self.is_available = True
            print("Mistral AI ONLINE!")
        except Exception as e:
            self.is_available = False
            print(f"Mistral offline: {e}\nFallback questions will be used.")

    def generate_questions(self, field, level, company, num=5, user_profile=None):
        if not self.is_available:
            return self._fallback_questions(field, level, company, num)

        company_lower = (company or 'default').lower()
        style = COMPANY_STYLES.get(company_lower, COMPANY_STYLES['default'])
        diff_key = (level or 'mid').lower()
        difficulty, diff_desc = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])

        profile_ctx = ""
        if user_profile:
            skills  = user_profile.get('skills', [])
            exp     = user_profile.get('experience_years', 0)
            role    = user_profile.get('current_role', '')
            summary = user_profile.get('resume_summary', '')
            if skills:  profile_ctx += f"\nCandidate skills: {', '.join(skills[:10])}"
            if exp:     profile_ctx += f"\nYears of experience: {exp}"
            if role:    profile_ctx += f"\nCurrent role: {role}"
            if summary: profile_ctx += f"\nBio: {summary[:250]}"

        prompt = f"""You are a senior interviewer at {company or 'a top tech company'}.

TARGET ROLE: {field}
LEVEL: {level} ({diff_desc})
COMPANY STYLE: {style}
{profile_ctx}

Generate EXACTLY {num} interview questions:
- Questions 1-2: Behavioral warm-up (easy-medium)
- Questions 3-4: Core technical ({difficulty})
- Question 5: Hard challenge (system design or complex scenario)

RULES:
- Relevant to {field} at {level} level
- 60%+ technical, up to 40% behavioral
- Each question needs 3-7 minutes to answer properly
- Output ONLY the numbered list, no extra text

1. [question]
2. [question]
3. [question]
4. [question]
5. [question]

BEGIN:"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900, temperature=0.75, top_p=0.95)
            raw = resp.choices[0].message.content
            qs  = self._parse_questions(raw, field, level, company, difficulty)
            if len(qs) < num:
                qs += self._fallback_questions(field, level, company, num - len(qs))
            return qs[:num]
        except Exception as e:
            app.logger.error(f"[Mistral] generate_questions: {e}")
            return self._fallback_questions(field, level, company, num)

    def analyze_answer(self, question, answer, field, level, company=''):
        if not self.is_available:
            return self._fallback_analysis(question, answer)

        style = COMPANY_STYLES.get((company or 'default').lower(), COMPANY_STYLES['default'])

        prompt = f"""You are a hiring manager at {company or 'a top tech company'} evaluating a {level} {field} candidate.

QUESTION: {question}
ANSWER: {answer}
COMPANY CONTEXT: {style}

Score on 6 dimensions (0.0-10.0 each):
1. TECHNICAL_ACCURACY - correctness of facts and approaches
2. DEPTH              - thoroughness of explanation
3. CLARITY            - organisation and ease of understanding
4. RELEVANCE          - how directly it addresses the question
5. COMMUNICATION      - professional language and vocabulary
6. CONFIDENCE         - decisiveness and ownership

OVERALL_SCORE = Technical*0.30 + Depth*0.20 + Clarity*0.20 + Relevance*0.15 + Communication*0.10 + Confidence*0.05

Output EXACTLY this format:
TECHNICAL_ACCURACY: [score]
DEPTH: [score]
CLARITY: [score]
RELEVANCE: [score]
COMMUNICATION: [score]
CONFIDENCE: [score]
OVERALL_SCORE: [score]
STRENGTHS:
- [point 1]
- [point 2]
- [point 3]
IMPROVEMENTS:
- [point 1]
- [point 2]
- [point 3]
DETAILED_FEEDBACK:
[2-3 paragraphs]
IMPROVEMENT_PLAN:
- [action 1]
- [action 2]
- [action 3]"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1100, temperature=0.3, top_p=0.9)
            return self._parse_analysis(resp.choices[0].message.content, answer)
        except Exception as e:
            app.logger.error(f"[Mistral] analyze_answer: {e}")
            return self._fallback_analysis(question, answer)

    def _parse_questions(self, text, field, level, company, difficulty):
        questions = []
        for line in text.strip().split('\n'):
            line = line.strip()
            m = re.match(r'^[\d]+[.)]\s*(.+)', line)
            if m:
                q_text = m.group(1).strip()
            elif line.startswith('-') and len(line) > 5:
                q_text = line.lstrip('- ').strip()
            else:
                continue
            if len(q_text) > 15:
                questions.append({
                    'text': q_text, 'category': 'technical',
                    'field': field, 'level': level, 'company': company,
                    'difficulty': difficulty,
                    'topic_tags': json.dumps([field.lower()]),
                })
        return questions

    def _parse_analysis(self, text, answer):
        def num(pattern, default=7.0):
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try: return min(10.0, max(0.0, float(m.group(1))))
                except: pass
            return default

        def bullets(marker):
            items, active = [], False
            for line in text.split('\n'):
                if marker.upper() in line.upper(): active = True; continue
                if active:
                    s = line.strip()
                    if s.startswith('-') and len(s) > 2: items.append(s.lstrip('- ').strip())
                    elif s and not s.startswith('-') and items: break
            return items

        def block(marker):
            idx = text.upper().find(marker.upper())
            if idx == -1: return ''
            blk = text[idx + len(marker):].strip()
            for m2 in re.finditer(r'\n[A-Z_]{5,}:', blk):
                blk = blk[:m2.start()]; break
            return blk.strip()

        ta   = num(r'TECHNICAL_ACCURACY\s*:\s*([\d.]+)')
        dep  = num(r'DEPTH\s*:\s*([\d.]+)')
        cla  = num(r'CLARITY\s*:\s*([\d.]+)')
        rel  = num(r'RELEVANCE\s*:\s*([\d.]+)')
        com  = num(r'COMMUNICATION\s*:\s*([\d.]+)')
        conf = num(r'CONFIDENCE\s*:\s*([\d.]+)')
        ov   = num(r'OVERALL_SCORE\s*:\s*([\d.]+)')
        computed = ta*0.30 + dep*0.20 + cla*0.20 + rel*0.15 + com*0.10 + conf*0.05
        overall  = round((ov + computed) / 2, 2)

        strengths    = bullets('STRENGTHS')        or ['Engaged with the question', 'Provided a relevant response']
        improvements = bullets('IMPROVEMENTS')     or ['Elaborate more on key points', 'Add concrete examples']
        plan         = bullets('IMPROVEMENT_PLAN') or [
            'Review core concepts for this topic',
            'Practice answering aloud in 150-300 words',
            'Complete 2 mock interviews this week',
        ]
        feedback = block('DETAILED_FEEDBACK:')
        if not feedback:
            wc = len(answer.split())
            feedback = f"Your {wc}-word answer scores {overall}/10. {'Good depth.' if wc > 80 else 'Try to elaborate more with examples.'}"

        return {
            'score': overall, 'technical_accuracy': ta, 'depth_score': dep,
            'clarity_score': cla, 'relevance_score': rel,
            'communication_score': com, 'confidence_score': conf,
            'strengths': strengths[:3], 'weaknesses': improvements[:3],
            'improvement_plan': plan[:3], 'feedback': feedback,
            'model': self.model_name,
        }

    def _fallback_questions(self, field, level, company, num):
        app.logger.info("[Mistral] Using fallback questions")
        try:
            bank = QuestionBank.query.filter(
                QuestionBank.field.ilike(f'%{field}%')).limit(num).all()
            if bank:
                return [{'text': q.text, 'category': q.category,
                          'field': field, 'level': level, 'company': company,
                          'difficulty': q.difficulty,
                          'topic_tags': q.topic_tags or json.dumps([field.lower()])}
                        for q in bank]
        except Exception:
            pass

        diff_key   = (level or 'mid').lower()
        difficulty = DIFFICULTY_MAP.get(diff_key, DIFFICULTY_MAP['default'])[0]
        field_low  = (field or 'software').lower()

        pools = {
            'software': [
                (f"Design a URL-shortening service for {company or 'millions of users'}. Walk through your architecture.", 'technical', 'hard'),
                ("What is the most complex bug you have debugged? How did you find and fix it?", 'behavioral', 'medium'),
                ("Explain the difference between a process and a thread and when you would use each.", 'technical', 'medium'),
                ("How does garbage collection work in your primary language? What are its performance trade-offs?", 'technical', 'medium'),
                ("Describe the CAP theorem. How would you balance consistency and availability for a payment system?", 'technical', 'hard'),
                ("Walk me through implementing rate-limiting on a high-traffic REST API.", 'technical', 'hard'),
                ("How do you ensure code quality in a fast-moving team?", 'behavioral', 'medium'),
            ],
            'data': [
                ("How do you handle class imbalance in a classification problem? Explain at least 3 techniques.", 'technical', 'medium'),
                (f"Explain overfitting and how you prevent it when building production models.", 'technical', 'medium'),
                ("Walk through your ML pipeline for predicting customer churn end-to-end.", 'technical', 'hard'),
                ("How do you evaluate a recommendation system? What metrics matter most?", 'technical', 'medium'),
                ("Describe a time you cleaned severely messy data. What was your process?", 'behavioral', 'medium'),
            ],
            'product': [
                (f"How would you measure success of {company or 'a new'}'s checkout feature?", 'technical', 'medium'),
                ("How do you prioritise a backlog when stakeholders have competing requests?", 'behavioral', 'medium'),
                ("How do you decide what NOT to build?", 'behavioral', 'hard'),
                ("Describe a product decision you made using data. What was the outcome?", 'behavioral', 'medium'),
                ("Design a feature to improve retention for a social media app.", 'technical', 'hard'),
            ],
        }

        pool_key = 'software'
        for k in pools:
            if k in field_low: pool_key = k; break

        return [
            {'text': text, 'category': cat, 'field': field, 'level': level, 'company': company,
             'difficulty': diff, 'topic_tags': json.dumps([field_low])}
            for text, cat, diff in pools[pool_key][:num]
        ]

    def _fallback_analysis(self, question, answer):
        wc    = len((answer or '').split())
        score = min(10.0, max(1.0, round(4.0 + wc * 0.06, 1)))
        return {
            'score': score, 'technical_accuracy': score,
            'depth_score': max(1.0, score-0.5), 'clarity_score': max(1.0, score-0.3),
            'relevance_score': score, 'communication_score': max(1.0, score-0.2),
            'confidence_score': max(1.0, score-0.5),
            'strengths': ['Engaged with the question', 'Provided a response', f'{wc} words written'],
            'weaknesses': ['AI offline - full scoring unavailable', 'Add specific examples'],
            'improvement_plan': [
                'Start LM Studio for live AI scoring',
                'Practice answering in 150-300 words',
                'Record and review your answers for clarity',
            ],
            'feedback': f"[AI Offline] Heuristic score: {score}/10 ({wc} words). Start LM Studio for full AI feedback.",
            'model': 'fallback-heuristic',
        }


# Initialise AI agent
mistral_agent = MistralAIAgent()
'''

PART3 = r'''

# ==============================================================================
#  API ENDPOINTS
# ==============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'mistral_available': mistral_agent.is_available,
        'version': '3.0.0-enterprise',
        'timestamp': datetime.now().isoformat()
    }), 200


# ── AUTH ────────────────────────────────────────────────────────────────────────

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json(force=True, silent=True) or {}
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400

        user = User(
            email=data['email'],
            first_name=data.get('first_name') or data.get('firstName', ''),
            last_name=data.get('last_name')  or data.get('lastName', ''),
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        app.logger.info(f"[Auth] Registered: {user.email} (ID {user.id})")
        token = create_access_token(identity=str(user.id))
        return jsonify({'message': 'Registration successful', 'access_token': token,
                        'user': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Auth] Register error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True, silent=True) or {}
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        if not user.is_active:
            return jsonify({'error': 'Account disabled. Contact support.'}), 403

        user.last_login = datetime.utcnow()
        db.session.commit()

        app.logger.info(f"[Auth] Login: {user.email} (ID {user.id})")
        token = create_access_token(identity=str(user.id))
        return jsonify({'message': 'Login successful', 'access_token': token,
                        'user': user.to_dict()}), 200
    except Exception as e:
        app.logger.error(f"[Auth] Login error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── USER PROFILE ────────────────────────────────────────────────────────────────

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        profile = user.to_dict()
        profile['resume_summary']   = user.resume_summary
        profile['linkedin_url']     = user.linkedin_url
        profile['github_url']       = user.github_url
        profile['headline']         = user.headline
        profile['education']        = json.loads(user.education or '[]')
        profile['target_roles']     = json.loads(user.target_roles or '[]')
        profile['total_questions_answered'] = user.total_questions_answered
        return jsonify(profile), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user: return jsonify({'error': 'User not found'}), 404
        data = request.get_json(force=True, silent=True) or {}

        for field_name in ['first_name','last_name','phone','linkedin_url','github_url',
                           'headline','resume_summary','current_role']:
            if field_name in data:
                setattr(user, field_name, data[field_name])
        if 'experience_years' in data:
            user.experience_years = int(data['experience_years'])
        if 'skills' in data:
            user.skills = json.dumps(data['skills'] if isinstance(data['skills'], list) else [data['skills']])
        if 'dream_companies' in data:
            user.dream_companies = json.dumps(data['dream_companies'] if isinstance(data['dream_companies'], list) else [])
        if 'target_roles' in data:
            user.target_roles = json.dumps(data['target_roles'] if isinstance(data['target_roles'], list) else [])
        if 'education' in data:
            user.education = json.dumps(data['education'] if isinstance(data['education'], list) else [])

        db.session.commit()
        return jsonify({'message': 'Profile updated', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ── INTERVIEW ────────────────────────────────────────────────────────────────────

@app.route('/api/interview/start', methods=['POST'])
@jwt_required()
def start_interview():
    try:
        user_id = int(get_jwt_identity())
        user    = db.session.get(User, user_id)
        if not user: return jsonify({'error': 'User not found'}), 404

        data    = request.get_json(force=True, silent=True) or {}
        field   = data.get('field', 'Software Engineering')
        level   = data.get('level', 'Mid')
        company = data.get('company', 'Tech Company')
        num_q   = min(int(data.get('num_questions', 5)), 10)

        app.logger.info(f"[Interview] Starting: User {user_id}, {field} ({level}) at {company}")

        # Snapshot user profile for AI personalisation
        profile_snap = {
            'skills': user.skills_list(),
            'experience_years': user.experience_years,
            'current_role': user.current_role,
            'resume_summary': user.resume_summary,
            'dream_companies': user.dream_companies_list(),
        }

        # Create interview record
        interview = Interview(
            user_id=user_id, field=field, level=level, company=company,
            interview_type='technical', status='in_progress', questions_total=num_q,
            ai_model_used=mistral_agent.model_name,
            user_profile_snapshot=json.dumps(profile_snap),
        )
        db.session.add(interview)
        db.session.commit()

        # Generate questions (AI or fallback)
        raw_qs = mistral_agent.generate_questions(field, level, company, num_q,
                                                   user_profile=profile_snap)

        stored_qs = []
        for i, qdata in enumerate(raw_qs):
            q = Question(
                interview_id=interview.id,
                text=qdata['text'],
                category=qdata.get('category', 'technical'),
                field=field, level=level, company=company,
                difficulty=qdata.get('difficulty', 'medium'),
                topic_tags=qdata.get('topic_tags', json.dumps([field.lower()])),
                question_number=i + 1,
                source='ai_generated',
            )
            db.session.add(q)
            stored_qs.append(q)
        db.session.commit()

        user.total_interviews += 1
        db.session.commit()

        app.logger.info(f"[Interview] Created {interview.id} with {len(stored_qs)} questions")
        return jsonify({
            'interview_id': interview.uuid,
            'interview': interview.to_dict(),
            'questions': [q.to_dict() for q in stored_qs],
            'mistral_active': mistral_agent.is_available,
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Interview] start_interview error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/submit', methods=['POST'])
@jwt_required()
def submit_answer(interview_uuid):
    try:
        user_id   = int(get_jwt_identity())
        data      = request.get_json(force=True, silent=True) or {}
        interview = Interview.query.filter_by(uuid=interview_uuid).first()

        if not interview:   return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id: return jsonify({'error': 'Unauthorized'}), 403

        question_id  = data.get('question_id')
        answer_text  = (data.get('answer', '') or '').strip()
        time_spent   = int(data.get('time_spent', 0))

        if not answer_text: return jsonify({'error': 'Answer text required'}), 400

        # Find question in this session (or allow by ID only)
        question = None
        if question_id:
            question = Question.query.filter_by(id=question_id,
                                                interview_id=interview.id).first()

        if not question and question_id:
            question = db.session.get(Question, question_id)

        if not question:
            return jsonify({'error': 'Question not found in this session'}), 404

        # AI analysis
        analysis = mistral_agent.analyze_answer(
            question=question.text,
            answer=answer_text,
            field=interview.field,
            level=interview.level,
            company=interview.company,
        )

        # Store answer with all dimensions
        answer = Answer(
            interview_id=interview.id,
            question_id=question.id,
            text=answer_text,
            word_count=len(answer_text.split()),
            score=analysis['score'],
            technical_accuracy=analysis['technical_accuracy'],
            depth_score=analysis['depth_score'],
            clarity_score=analysis['clarity_score'],
            relevance_score=analysis['relevance_score'],
            communication_score=analysis['communication_score'],
            confidence_score=analysis['confidence_score'],
            time_spent_seconds=time_spent,
        )
        db.session.add(answer)
        db.session.commit()

        # Store feedback
        feedback = Feedback(
            user_id=user_id,
            answer_id=answer.id,
            score=analysis['score'],
            strengths=json.dumps(analysis['strengths']),
            improvements=json.dumps(analysis['weaknesses']),
            detailed_feedback=analysis['feedback'],
            improvement_plan=json.dumps(analysis.get('improvement_plan', [])),
            model_used=analysis.get('model', 'unknown'),
        )
        db.session.add(feedback)

        # Update interview progress
        interview.questions_answered += 1
        db.session.commit()

        # Update user totals
        user = db.session.get(User, user_id)
        if user:
            user.total_questions_answered += 1
            db.session.commit()

        app.logger.info(f"[Interview] Answer stored: Q{question.question_number}, Score={analysis['score']}")
        return jsonify({
            'answer_id': answer.uuid,
            'question_number': question.question_number,
            'analysis': {
                'score': analysis['score'],
                'technical_accuracy': analysis['technical_accuracy'],
                'depth_score': analysis['depth_score'],
                'clarity_score': analysis['clarity_score'],
                'relevance_score': analysis['relevance_score'],
                'communication_score': analysis['communication_score'],
                'confidence_score': analysis['confidence_score'],
                'strengths': analysis['strengths'],
                'weaknesses': analysis['weaknesses'],
                'feedback': analysis['feedback'],
                'improvement_plan': analysis.get('improvement_plan', []),
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Interview] submit_answer error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/complete', methods=['POST'])
@jwt_required()
def complete_interview(interview_uuid):
    try:
        user_id   = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid).first()
        if not interview:   return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id: return jsonify({'error': 'Unauthorized'}), 403

        answers = Answer.query.filter_by(interview_id=interview.id).all()
        scored  = [a for a in answers if a.score is not None]

        overall     = round(sum(a.score for a in scored) / len(scored), 2) if scored else 0.0
        tech_avg    = round(sum(a.technical_accuracy or 0 for a in scored) / max(len(scored),1), 2)
        comm_avg    = round(sum(a.communication_score or 0 for a in scored) / max(len(scored),1), 2)
        clarity_avg = round(sum(a.clarity_score or 0 for a in scored) / max(len(scored),1), 2)
        depth_avg   = round(sum(a.depth_score or 0 for a in scored) / max(len(scored),1), 2)

        def grade(s):
            if s >= 9.0: return 'A+'
            if s >= 8.0: return 'A'
            if s >= 7.0: return 'B'
            if s >= 6.0: return 'C'
            if s >= 5.0: return 'D'
            return 'F'

        interview.status             = 'completed'
        interview.completed_at       = datetime.utcnow()
        interview.overall_score      = overall
        interview.technical_score    = tech_avg
        interview.communication_score= comm_avg
        interview.clarity_score      = clarity_avg
        interview.depth_score        = depth_avg
        interview.performance_grade  = grade(overall)
        if interview.started_at:
            interview.duration_seconds = int((datetime.utcnow() - interview.started_at).total_seconds())

        # Update user aggregate stats
        user = db.session.get(User, user_id)
        if user:
            completed_all = Interview.query.filter_by(user_id=user_id, status='completed').all()
            scores = [i.overall_score for i in completed_all if i.overall_score is not None]
            user.average_score     = round(sum(scores) / len(scores), 2) if scores else 0.0
            user.best_score        = round(max(scores), 2) if scores else 0.0
            user.total_practice_time += (interview.duration_seconds or 0)
            user.last_activity_date = datetime.utcnow().date()

        db.session.commit()

        app.logger.info(f"[Interview] Completed {interview.id} | Score: {overall} | Grade: {grade(overall)}")
        return jsonify({
            'message': 'Interview completed',
            'interview': interview.to_dict(),
            'overall_score': overall,
            'performance_grade': grade(overall),
            'breakdown': {
                'technical': tech_avg,
                'communication': comm_avg,
                'clarity': clarity_avg,
                'depth': depth_avg,
            },
            'total_answered': len(scored),
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"[Interview] complete error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/history', methods=['GET'])
@jwt_required()
def interview_history():
    try:
        user_id = int(get_jwt_identity())
        page    = int(request.args.get('page', 1))
        per_page= min(int(request.args.get('per_page', 10)), 50)
        status  = request.args.get('status')

        q = Interview.query.filter_by(user_id=user_id)
        if status: q = q.filter_by(status=status)
        q = q.order_by(Interview.started_at.desc())
        total   = q.count()
        sessions= q.offset((page-1)*per_page).limit(per_page).all()

        return jsonify({
            'sessions': [s.to_dict() for s in sessions],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/interview/<interview_uuid>/full-report', methods=['GET'])
@jwt_required()
def full_report(interview_uuid):
    try:
        user_id   = int(get_jwt_identity())
        interview = Interview.query.filter_by(uuid=interview_uuid).first()
        if not interview:   return jsonify({'error': 'Interview not found'}), 404
        if interview.user_id != user_id: return jsonify({'error': 'Unauthorized'}), 403

        answers = Answer.query.filter_by(interview_id=interview.id).all()
        qa_pairs = []
        for a in answers:
            question = db.session.get(Question, a.question_id) if a.question_id else None
            fb       = Feedback.query.filter_by(answer_id=a.id).first()
            qa_pairs.append({
                'question': question.to_dict() if question else None,
                'answer':   a.to_dict(),
                'feedback': fb.to_dict() if fb else None,
            })

        return jsonify({
            'interview': interview.to_dict(),
            'qa_pairs': qa_pairs,
            'total_questions_answered': len(answers),
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── DASHBOARD ──────────────────────────────────────────────────────────────────

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    try:
        user_id = int(get_jwt_identity())
        user    = db.session.get(User, user_id)
        if not user: return jsonify({'error': 'User not found'}), 404

        recent = Interview.query.filter_by(user_id=user_id)\
                          .order_by(Interview.started_at.desc()).limit(5).all()
        completed_count = Interview.query.filter_by(user_id=user_id, status='completed').count()

        return jsonify({
            'total_interviews':          user.total_interviews,
            'total_questions_answered':  user.total_questions_answered,
            'average_score':             round(user.average_score or 0.0, 2),
            'avg_score':                 round(user.average_score or 0.0, 2),
            'best_score':                round(user.best_score or 0.0, 2),
            'current_streak':            user.current_streak or 0,
            'longest_streak':            user.longest_streak or 0,
            'total_practice_time':       user.total_practice_time or 0,
            'completed_interviews':      completed_count,
            'recent_sessions':           [s.to_dict() for s in recent],
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ERROR HANDLERS ──────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


# ==============================================================================
#  MAIN
# ==============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Seed demo user
        if not User.query.filter_by(email='demo@interviewcoach.ai').first():
            demo = User(email='demo@interviewcoach.ai', first_name='Demo', last_name='User',
                        headline='Full Stack Developer | AI Enthusiast',
                        experience_years=3, current_role='Software Developer',
                        skills=json.dumps(['Python','JavaScript','React','Node.js','SQL','Docker']),
                        dream_companies=json.dumps(['Google','Amazon','Microsoft']),
                        target_roles=json.dumps(['Senior Software Engineer','Backend Engineer']))
            demo.set_password('demo123456')
            db.session.add(demo)
            db.session.commit()
            print("[DB] Demo user created: demo@interviewcoach.ai / demo123456")
        else:
            print("[DB] Demo user already exists")

        # Seed QuestionBank with verified questions
        if QuestionBank.query.count() == 0:
            seed_qs = [
                QuestionBank(text="Design a scalable URL-shortening service. Walk through your system design.", category='technical', field='software', level='senior', company='google', difficulty='hard', is_verified=True),
                QuestionBank(text="Explain the difference between a process and a thread and when you'd use each.", category='technical', field='software', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="How do you handle class imbalance in a machine learning classification problem?", category='technical', field='data-science', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="Describe a time you resolved a conflict with a teammate. What was the outcome?", category='behavioral', field='software', level='mid', difficulty='easy', is_verified=True),
                QuestionBank(text="How would you measure success of a new product feature launch?", category='technical', field='product', level='mid', difficulty='medium', is_verified=True),
                QuestionBank(text="Explain CAP theorem and how you'd design a payment system given those constraints.", category='technical', field='software', level='senior', difficulty='hard', is_verified=True),
            ]
            db.session.add_all(seed_qs)
            db.session.commit()
            print(f"[DB] Seeded {len(seed_qs)} verified questions to QuestionBank")

    print("\n" + "="*70)
    print("  AI INTERVIEW COACH - ENTERPRISE BACKEND v3.0")
    print("="*70)
    print(f"  Database: {os.path.join(basedir,'interview_coach.db')}")
    print(f"  Mistral:  {'ONLINE' if mistral_agent.is_available else 'OFFLINE (fallback active)'}")
    print(f"  Server:   http://127.0.0.1:5000")
    print("="*70 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
'''

with open('app.py', 'a', encoding='utf-8') as f:
    f.write(PART2)
    f.write(PART3)

print("Done. Total lines:", open('app.py', encoding='utf-8').read().count('\n'))
