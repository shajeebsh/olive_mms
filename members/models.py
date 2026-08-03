from django.db import models

from core.models import TimeStampedModel


class Family(TimeStampedModel):
    name = models.CharField(max_length=150)
    head = models.CharField(max_length=150, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "families"

    def __str__(self):
        return self.name


class Member(TimeStampedModel):
    class MembershipStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        FRIEND = "FRIEND", "Friend"

    class MemberRole(models.TextChoices):
        IMAM = "IMAM", "Imam"
        MUAZZIN = "MUAZZIN", "Muazzin"
        TEACHER = "TEACHER", "Teacher"
        VOLUNTEER = "VOLUNTEER", "Volunteer"
        DONOR = "DONOR", "Donor"
        MEMBER = "MEMBER", "Member"

    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    join_date = models.DateField(null=True, blank=True)
    membership_status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )
    member_role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.MEMBER,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    def whatsapp_number(self):
        """Digits-only phone suitable for https://wa.me/ links."""
        return "".join(ch for ch in self.phone if ch.isdigit())

    def whatsapp_url(self, message=None):
        url = f"https://wa.me/{self.whatsapp_number()}"
        if message:
            from urllib.parse import quote

            url += f"?text={quote(message)}"
        return url
