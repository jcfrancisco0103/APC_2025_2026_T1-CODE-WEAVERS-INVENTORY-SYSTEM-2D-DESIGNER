from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
import uuid
from datetime import datetime
from django.utils import timezone
from .models import ChatSession, ChatMessage, ChatbotKnowledge, Customer
from django.db.models import Q
import re

# Import admin_required decorator from views
from .views import admin_required


class ChatbotService:
    """Service class to handle chatbot logic and responses"""
    
    def __init__(self):
        self.default_responses = {
            'greeting': [
                "Hello! Welcome to WorksTeamWear! I'm here to help you with any questions about our products, orders, or services. How can I assist you today?",
                "Hi there! I'm your WorksTeamWear assistant. I can help you with product information, ordering, account questions, and more. What would you like to know?"
            ],
            'goodbye': [
                "Thank you for chatting with WorksTeamWear! If you need any more help, feel free to ask. Have a great day!",
                "Goodbye! Don't hesitate to reach out if you have more questions. Happy shopping at WorksTeamWear!"
            ],
            'default': [
                "I'm here to help! Could you please provide more details about what you're looking for? I can assist with:\n• Product information and availability\n• Order status and tracking\n• Account management\n• Shipping and delivery\n• Payment methods\n• Product customization\n• Returns and refunds",
                "I'd be happy to help you with that! For the best assistance, could you tell me more about:\n• What specific product you're interested in?\n• If you need help with an existing order?\n• Account or payment questions?\n• Information about our customization services?"
            ]
        }
    
    def get_response(self, user_message, session_id=None):
        """Generate appropriate response based on user message"""
        user_message_lower = user_message.lower().strip()
        
        # Check for greeting patterns
        if self._is_greeting(user_message_lower):
            return self._get_random_response('greeting')
        
        # Check for goodbye patterns
        if self._is_goodbye(user_message_lower):
            return self._get_random_response('goodbye')
        
        # Search knowledge base for relevant response
        knowledge_response = self._search_knowledge_base(user_message_lower)
        if knowledge_response:
            return knowledge_response
        
        # Check for specific patterns and provide contextual responses
        contextual_response = self._get_contextual_response(user_message_lower)
        if contextual_response:
            return contextual_response
        
        # Check if admin help is needed
        if self._needs_admin_help(user_message_lower, session_id):
            return self._request_admin_help(session_id, user_message)
        
        # Default response
        return self._get_random_response('default')
    
    def _is_greeting(self, message):
        greeting_patterns = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
        return any(pattern in message for pattern in greeting_patterns)
    
    def _is_goodbye(self, message):
        goodbye_patterns = ['bye', 'goodbye', 'see you', 'thanks', 'thank you', 'that\'s all', 'done']
        return any(pattern in message for pattern in goodbye_patterns)
    
    def _search_knowledge_base(self, message):
        """Search the knowledge base for relevant responses"""
        try:
            knowledge_items = ChatbotKnowledge.objects.filter(is_active=True)
            
            for item in knowledge_items:
                keywords = item.get_keywords_list()
                if any(keyword in message for keyword in keywords):
                    return item.answer
            
            return None
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return None
    
    def _get_contextual_response(self, message):
        """Provide contextual responses based on message content"""
        
        # Order-related queries
        if any(word in message for word in ['order', 'track', 'delivery', 'shipping']):
            return "I can help you with order-related questions! To track your order, you'll need your order reference number. You can find this in your email confirmation or by logging into your account and checking 'My Orders'. If you need specific help with an order, please provide your order reference number."
        
        # Product-related queries
        if any(word in message for word in ['product', 'jersey', 'shirt', 'size', 'color', 'design']):
            return "I'd be happy to help you with our products! We offer custom jerseys and teamwear in various sizes (XS, S, M, L, XL) and colors. You can browse our product catalog on the main page, or use our AI Designer tool to create custom designs. What specific product information are you looking for?"
        
        # Account-related queries
        if any(word in message for word in ['account', 'login', 'register', 'profile', 'password']):
            return "For account-related help: You can create an account by clicking 'Sign Up' in the top menu. If you're having trouble logging in, make sure you're using the correct email and password. You can reset your password using the 'Forgot Password' link on the login page. Need help with your profile information? You can update it in the 'My Profile' section after logging in."
        
        # Payment-related queries
        if any(word in message for word in ['payment', 'pay', 'gcash', 'cod', 'cash on delivery']):
            return "We accept multiple payment methods for your convenience: Cash on Delivery (COD) and GCash. You can select your preferred payment method during checkout. For COD orders, you'll pay when your order is delivered. For GCash payments, you'll be redirected to complete the payment securely."
        
        # Customization queries
        if any(word in message for word in ['custom', 'design', 'personalize', 'ai designer']):
            return "Our AI Designer tool lets you create custom jersey designs! You can access it from the main menu. The tool allows you to choose colors, add text, select patterns, and create unique designs for your team. You can also upload your own images or logos. Would you like me to guide you through the customization process?"
        
        return None
    
    def _get_random_response(self, response_type):
        """Get a random response from the specified type"""
        import random
        responses = self.default_responses.get(response_type, self.default_responses['default'])
        return random.choice(responses)
    
    def _needs_admin_help(self, message, session_id):
        """Determine if the message requires admin intervention"""
        # Keywords that indicate complex queries needing human help
        admin_help_keywords = [
            'speak to human', 'talk to person', 'human agent', 'customer service',
            'complaint', 'refund', 'cancel order', 'problem with order',
            'billing issue', 'payment problem', 'technical issue', 'bug',
            'not working', 'error', 'broken', 'defective', 'damaged',
            'urgent', 'emergency', 'escalate', 'manager', 'supervisor'
        ]
        
        # Check if message contains admin help keywords
        if any(keyword in message for keyword in admin_help_keywords):
            return True
        
        # Check if this is a complex query that bot couldn't handle
        # (multiple failed attempts or very specific technical questions)
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
                recent_messages = session.messages.filter(message_type='bot').order_by('-timestamp')[:3]
                
                # If last 3 bot responses were default responses, escalate
                default_responses_count = 0
                for msg in recent_messages:
                    if any(default_phrase in msg.content.lower() for default_phrase in 
                          ['sorry, i don\'t understand', 'i\'m not sure', 'could you please rephrase']):
                        default_responses_count += 1
                
                if default_responses_count >= 2:
                    return True
                    
            except ChatSession.DoesNotExist:
                pass
        
        return False
    
    def _request_admin_help(self, session_id, user_message):
        """Request admin help and update session status"""
        from django.utils import timezone
        
        try:
            session = ChatSession.objects.get(session_id=session_id)
            if session.handover_status == 'bot':
                session.handover_status = 'requested'
                session.handover_requested_at = timezone.now()
                session.handover_reason = f"User query: {user_message[:200]}"
                session.save()
                
                # Create system message about handover
                ChatMessage.objects.create(
                    session=session,
                    message_type='system',
                    content='Admin help has been requested for this conversation.'
                )
                
                return ("I understand you need additional assistance. I'm connecting you with one of our "
                       "customer service representatives who will be able to help you better. Please wait "
                       "a moment while I transfer your conversation.")
        except ChatSession.DoesNotExist:
            pass
        
        return ("I'd like to connect you with a human agent for better assistance. "
               "Please wait while I transfer your conversation.")


@csrf_protect
@require_http_methods(["POST"])
def chat_message(request):
    """Handle incoming chat messages"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get customer instance if user is authenticated
        customer_instance = None
        if request.user.is_authenticated:
            try:
                customer_instance = Customer.objects.get(user=request.user)
            except Customer.DoesNotExist:
                customer_instance = None
        
        # Get or create chat session
        chat_session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'customer': customer_instance,
                'is_active': True
            }
        )
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='user',
            content=message
        )
        
        # Generate bot response
        chatbot_service = ChatbotService()
        bot_response = chatbot_service.get_response(message, session_id)
        
        # Save bot response
        bot_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='bot',
            content=bot_response
        )
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'bot_response': bot_response,
            'timestamp': bot_message.timestamp.isoformat(),
            'handover_requested': chat_session.handover_status == 'requested'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Customer Support Chat API Endpoints

@csrf_exempt
@require_http_methods(["POST"])
def support_start_session(request):
    """Start a new customer support chat session"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        # Get or create customer if user is authenticated
        customer = None
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
            except Customer.DoesNotExist:
                pass
        
        # Get or create chat session
        session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'customer': customer,
                'handover_status': 'requested',  # Start as support request
                'handover_requested_at': timezone.now(),
                'handover_reason': 'Customer initiated support chat'
            }
        )
        
        if created:
            # Create welcome message
            ChatMessage.objects.create(
                session=session,
                message_type='system',
                content='Welcome to customer support! An agent will be with you shortly.'
            )
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'status': session.handover_status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def support_send_message(request):
    """Send a message in customer support chat"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        message_type = data.get('message_type', 'user')
        
        if not session_id or not message:
            return JsonResponse({'error': 'Session ID and message are required'}, status=400)
        
        # Get chat session
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Chat session not found'}, status=404)
        
        # Determine admin user for admin messages
        admin_user = None
        if message_type == 'admin' and request.user.is_authenticated and request.user.is_staff:
            admin_user = request.user
            # Update session to show admin is handling
            if session.handover_status == 'requested':
                session.handover_status = 'admin'
                session.admin_user = admin_user
                session.admin_joined_at = timezone.now()
                session.save()
        
        # Create message
        chat_message = ChatMessage.objects.create(
            session=session,
            message_type=message_type,
            content=message,
            admin_user=admin_user
        )
        
        return JsonResponse({
            'success': True,
            'message_id': chat_message.id,
            'timestamp': chat_message.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def support_request_new_agent(request):
    """Request a new agent for support chat"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Chat session not found'}, status=404)
        
        # Reset admin assignment and request new handover
        session.admin_user = None
        session.admin_joined_at = None
        session.handover_status = 'requested'
        session.save()
        
        # Create system message
        ChatMessage.objects.create(
            session=session,
            message_type='system',
            content='A new agent has been requested. Please wait while we connect you with another support representative.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'New agent requested successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def support_chat_history(request):
    """Get chat history for a support session"""
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Chat session not found'}, status=404)
        
        # Get messages
        messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        messages_data = []
        for msg in messages:
            # Determine sender name based on message type
            sender_name = 'System'  # Default
            if msg.message_type == 'user':
                if session.customer:
                    sender_name = f"{session.customer.user.first_name} {session.customer.user.last_name}".strip() or session.customer.user.username
                else:
                    sender_name = 'Customer'
            elif msg.message_type == 'admin':
                if msg.admin_user:
                    sender_name = f"{msg.admin_user.first_name} {msg.admin_user.last_name}".strip() or msg.admin_user.username
                else:
                    sender_name = 'Support Agent'
            elif msg.message_type == 'bot':
                sender_name = 'Bot Assistant'
            
            messages_data.append({
                'id': msg.id,
                'message_type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'sender_name': sender_name,
                'admin_user': msg.admin_user.username if msg.admin_user else None
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'session_status': session.handover_status
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def support_new_messages(request):
    """Get new messages since last check"""
    try:
        session_id = request.GET.get('session_id')
        last_id_param = request.GET.get('last_id', '0')
        
        # Handle NaN and invalid values
        try:
            last_id = int(last_id_param) if last_id_param and last_id_param != 'NaN' else 0
        except (ValueError, TypeError):
            last_id = 0
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Chat session not found'}, status=404)
        
        # Get new messages
        messages = ChatMessage.objects.filter(
            session=session,
            id__gt=last_id
        ).order_by('timestamp')
        
        messages_data = []
        for msg in messages:
            # Determine sender name based on message type
            sender_name = 'System'  # Default
            if msg.message_type == 'user':
                if session.customer:
                    sender_name = f"{session.customer.user.first_name} {session.customer.user.last_name}".strip() or session.customer.user.username
                else:
                    sender_name = 'Customer'
            elif msg.message_type == 'admin':
                if msg.admin_user:
                    sender_name = f"{msg.admin_user.first_name} {msg.admin_user.last_name}".strip() or msg.admin_user.username
                else:
                    sender_name = 'Support Agent'
            elif msg.message_type == 'bot':
                sender_name = 'Bot Assistant'
            
            messages_data.append({
                'id': msg.id,
                'message_type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'sender_name': sender_name,
                'admin_user': msg.admin_user.username if msg.admin_user else None
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'session_status': session.handover_status
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_protect
@require_http_methods(["GET"])
def chat_history(request):
    """Get chat history for a session"""
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Chat session not found'}, status=404)
        
        messages = chat_session.messages.all()
        
        message_data = []
        for msg in messages:
            # Determine sender name based on message type
            sender_name = 'System'
            if msg.message_type == 'user':
                if chat_session.customer and chat_session.customer.user:
                    sender_name = f"{chat_session.customer.user.first_name} {chat_session.customer.user.last_name}".strip()
                    if not sender_name:
                        sender_name = chat_session.customer.user.username
                else:
                    sender_name = 'Customer'
            elif msg.message_type == 'admin':
                if msg.admin_user:
                    sender_name = f"{msg.admin_user.first_name} {msg.admin_user.last_name}".strip()
                    if not sender_name:
                        sender_name = msg.admin_user.username
                else:
                    sender_name = 'Admin'
            elif msg.message_type == 'bot':
                sender_name = 'Bot Assistant'
            
            message_data.append({
                'message_type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'sender_name': sender_name
            })
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'messages': message_data,
            'handover_status': chat_session.handover_status,
            'is_active': chat_session.is_active
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def chat_feedback(request):
    """Handle user feedback on bot responses"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message_id = data.get('message_id')
        is_helpful = data.get('is_helpful')
        
        if not all([session_id, message_id, is_helpful is not None]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
            message = chat_session.messages.get(id=message_id, message_type='bot')
            message.is_helpful = is_helpful
            message.save()
            
            return JsonResponse({'success': True})
            
        except (ChatSession.DoesNotExist, ChatMessage.DoesNotExist):
            return JsonResponse({'error': 'Session or message not found'}, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def chatbot_widget(request):
    """Render the chatbot widget template"""
    return render(request, 'ecom/chatbot_widget.html')


@admin_required
@csrf_protect
@require_http_methods(["GET"])
def admin_pending_handovers(request):
    """Get list of chat sessions pending admin handover"""
    try:
        
        pending_sessions = ChatSession.objects.filter(
            handover_status='requested',
            is_active=True
        ).select_related('customer__user').order_by('handover_requested_at')
        
        sessions_data = []
        for session in pending_sessions:
            try:
                # Get latest messages for context
                latest_messages = session.messages.order_by('-timestamp')[:5]
                messages_data = []
                for msg in reversed(latest_messages):
                    messages_data.append({
                        'type': msg.message_type,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat()
                    })
                
                customer_name = 'Anonymous'
                if session.customer and session.customer.user:
                    customer_name = f"{session.customer.user.first_name} {session.customer.user.last_name}".strip()
                    if not customer_name:
                        customer_name = session.customer.user.username
                
                session_data = {
                    'session_id': session.session_id,
                    'customer_name': customer_name,
                    'handover_requested_at': session.handover_requested_at.isoformat() if session.handover_requested_at else None,
                    'handover_reason': session.handover_reason or 'No reason provided',
                    'recent_messages': messages_data
                }
                
                sessions_data.append(session_data)
                
            except Exception as e:
                # Log the error but continue processing other sessions
                continue
        
        return JsonResponse({
            'success': True,
            'pending_handovers': sessions_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def admin_take_handover(request):
    """Admin takes over a chat session"""
    try:
        # Check authentication for AJAX requests
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        session = ChatSession.objects.get(session_id=session_id)
        
        if session.handover_status != 'requested':
            return JsonResponse({'error': 'Session is not pending handover'}, status=400)
        
        from django.utils import timezone
        session.handover_status = 'admin'
        session.admin_user = request.user
        session.admin_joined_at = timezone.now()
        session.save()
        
        # Create system message about admin takeover
        ChatMessage.objects.create(
            session=session,
            message_type='system',
            content=f'Admin {request.user.first_name or request.user.username} has joined the conversation.'
        )
        
        # Create automated message when admin takes over
        ChatMessage.objects.create(
            session=session,
            message_type='admin',
            content='Thank you for contacting WorksTeamWear.\n\nPlease note that this conversation may be recorded or monitored for training and quality assurance purposes. This helps us improve our service and ensure your experience is as smooth and helpful as possible.\nIf you have any concerns, feel free to let us know.',
            admin_user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully took over the conversation'
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Chat session not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def admin_send_message(request):
    """Admin sends a message in a chat session"""
    try:
        # Check authentication for AJAX requests
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message_content = data.get('message', '').strip()
        
        if not session_id or not message_content:
            return JsonResponse({'error': 'Session ID and message are required'}, status=400)
        
        session = ChatSession.objects.get(session_id=session_id)
        
        if session.handover_status != 'admin' or session.admin_user != request.user:
            return JsonResponse({'error': 'You are not handling this conversation'}, status=403)
        
        # Create admin message
        admin_message = ChatMessage.objects.create(
            session=session,
            message_type='admin',
            content=message_content,
            admin_user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message_id': admin_message.id,
            'timestamp': admin_message.timestamp.isoformat()
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Chat session not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_protect
@require_http_methods(["POST"])
def admin_resolve_handover(request):
    """Mark a handover as resolved"""
    try:
        # Check authentication for AJAX requests
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'Session ID is required'}, status=400)
        
        session = ChatSession.objects.get(session_id=session_id)
        
        if session.admin_user != request.user:
            return JsonResponse({'error': 'You are not handling this conversation'}, status=403)
        
        session.handover_status = 'resolved'
        session.save()
        
        # Create system message about resolution
        ChatMessage.objects.create(
            session=session,
            message_type='system',
            content='This conversation has been resolved by admin.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Conversation marked as resolved'
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Chat session not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)