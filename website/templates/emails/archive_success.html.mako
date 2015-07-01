<%inherit file="notify_base.mako" />

<%def name="content()">
<tr>
  <td style="border-collapse: collapse;">
<<<<<<< HEAD
    <h3 class="text-center" style="padding: 0;margin: 30px 0 0 0;border: none;list-style: none;font-weight: 300;text-align: center;">Registration of ${src.title} finished</h3>
=======
    <h3 class="text-center" style="padding: 0;margin: 30px 0 0 0;border: none;list-style: none;font-weight: 300;text-align: center;">Registration of <b>${src.title}</b> finished</h3>
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798
  </td>
</tr>
<tr>
  <td style="border-collapse: collapse;">
    <% from website import settings %>
    You can view the registration <a href="${settings.DOMAIN.rstrip('/') + src.url}">here.</a>
  </td>
</tr>
</%def>
