from django.db.models import Q, Case, When, Value, IntegerField
from django.core.cache import cache
from config.user.models import User
from config.profiles.models import Profile
from .models import Interest, UserInterest, SearchHistory


class InterestService:
    @staticmethod
    def add_interest(user, interest_name, score=1):
        """Qiziqishni qo'shish, ballni yangilash va keshni tozalash"""
        interest_name = interest_name.strip().lower()
        if not interest_name or len(interest_name) < 2:
            return None

        interest, _ = Interest.objects.get_or_create(name=interest_name)
        user_interest, created = UserInterest.objects.get_or_create(
            user=user, interest=interest,
            defaults={"score": score}
        )

        if not created:
            user_interest.score += score
            user_interest.save(update_fields=["score", "updated_at"])

        # Foydalanuvchi qiziqishi o'zgargani uchun keshni o'chiramiz
        cache.delete(f"search_suggest_{user.id}")
        return user_interest

    @staticmethod
    def process_search_query(user, query, ip_address=None):
        """Qidiruvni tarixga saqlash va so'zlarni tahlil qilib ballash"""
        query = query.strip()
        if not query:
            return

        # 1. Tarixga saqlash
        SearchHistory.objects.create(user=user, query=query, ip_address=ip_address)

        # 2. So'zlarga bo'lib ball berish (3 harfdan uzun so'zlar)
        parts = [p.strip().lower() for p in query.split() if len(p.strip()) > 2]
        for part in parts:
            InterestService.add_interest(user, part, score=1)

    @staticmethod
    def boost_interest_on_click(user, profile_owner):
        """Profilga kirganda (click) ballni keskin oshirish"""
        if not hasattr(profile_owner, 'profile'):
            return

        words = []
        if profile_owner.profile.full_name:
            words.extend(profile_owner.profile.full_name.split())
        if profile_owner.profile.username:
            words.append(profile_owner.profile.username)

        for word in words:
            if len(word) > 2:
                InterestService.add_interest(user, word, score=5)


class UserSearchService:
    @staticmethod
    def search(user, query: str):
        """Aniq qidiruv mantiqi (Relevance bo'yicha)"""
        query = query.strip()
        if not query:
            return User.objects.none()

        parts = [p.strip() for p in query.split() if p.strip()]

        # Filtirlash: hamma so'zlar ishtirok etishi shart (&)
        filters = Q()
        for part in parts:
            filters &= (Q(profile__username__icontains=part) | Q(profile__full_name__icontains=part))

        return User.objects.select_related("profile").filter(filters).exclude(id=user.id).annotate(
            relevance=Case(
                When(profile__username__iexact=query, then=Value(100)),
                When(profile__full_name__iexact=query, then=Value(95)),
                When(profile__username__istartswith=query, then=Value(85)),
                default=Value(50),
                output_field=IntegerField(),
            )
        ).order_by("-relevance", "-id").distinct()[:20]

    @staticmethod
    def suggest(user):
        """Redis keshga asoslangan shaxsiy tavsiyalar mantiqi"""
        cache_key = f"search_suggest_{user.id}"
        cached_users = cache.get(cache_key)

        if cached_users is not None:
            return cached_users

        # 1. Foydalanuvchining eng kuchli qiziqishlarini bazadan olamiz
        top_interests = (
            UserInterest.objects.filter(user=user)
            .select_related("interest")
            .order_by("-score")[:10]
        )

        if not top_interests:
            # Fallback: Agar qiziqish bo'lmasa, eng yangi foydalanuvchilar
            users = list(User.objects.select_related("profile").exclude(id=user.id).order_by("-id")[:20])
        else:
            filters = Q()
            when_clauses = []

            for ui in top_interests:
                name = ui.interest.name
                weight = ui.score

                filters |= Q(profile__username__icontains=name)
                filters |= Q(profile__full_name__icontains=name)
                filters |= Q(profile__bio__icontains=name)

                # Dinamik vazn: bazadagi score qancha baland bo'lsa, tavsiya shuncha yuqorida chiqadi
                when_clauses.append(When(profile__username__icontains=name, then=Value(weight * 2)))
                when_clauses.append(When(profile__full_name__icontains=name, then=Value(weight)))

            users = list(
                User.objects.select_related("profile")
                .filter(filters)
                .exclude(id=user.id)
                .annotate(
                    relevance=Case(
                        *when_clauses,
                        default=Value(1),
                        output_field=IntegerField()
                    )
                )
                .order_by("-relevance", "-id")
                .distinct()[:20]
            )

        # Natijani 15 daqiqaga keshga saqlaymiz
        cache.set(cache_key, users, timeout=900)
        return users